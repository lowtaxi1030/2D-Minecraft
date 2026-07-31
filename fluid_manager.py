import config
import tool


class FluidManager:
    def __init__(self, chunks):
        self.chunks = chunks

        self.active_fluids = {"water": set(), "lava": set()}
        self.next_active_fluids = {"water": set(), "lava": set()}

        self.FLUID_PROPERTIES = {
            "water": {
                # "max_spread": 7,  # 最大擴散距離
                "max_level": 8,
                "update_delay": 300,  # 更新頻率 (ms)
                "last_update_time": 0,
                "flow_block": "water_flow",
                "source_block": "water_source",
            },
            "lava": {
                # "max_spread": 5,  # 岩漿擴散較短
                "max_level": 6,
                "update_delay": 550,  # 岩漿流得很慢  (ms)
                "last_update_time": 0,
                "flow_block": "lava_flow",
                "source_block": "lava_source",
            },
        }

        self.all_fluid_blocks = {f"{fluid}_{t}" for fluid in self.FLUID_PROPERTIES for t in ("flow", "source")}

    def register_chunk_fluids(self, chunk_x):
        """當 chunk 被生成時，呼叫此方法將 chunk 中的水源加入 active_fluids"""
        chunk = self.chunks[chunk_x]
        for fluid in self.FLUID_PROPERTIES.keys():
            fluid_data = self.FLUID_PROPERTIES[fluid]
            for y in range(config.MAP_HEIGHT):
                for local_x in range(config.CHUNK_WIDTH):
                    block = chunk.blocks[y][local_x]
                    if block == fluid_data["source_block"]:
                        world_x = chunk_x * config.CHUNK_WIDTH + local_x
                        self.active_fluids[fluid].add((world_x, y))

    def add_fluid(self, world_x: int, world_y: int, fluid_type: str):
        """當玩家放置水，或是地圖生成水源時呼叫此方法"""
        self.active_fluids[fluid_type].add((world_x, world_y))

    def wake_fluid(self, fluid_type: str, x: int, y: int, target: dict[str, set] = None):
        """target 永遠代表「整個 active dictionary」"""

        if target is None:
            target = self.active_fluids

        for nx, ny in self._neighbors(x, y):
            target[fluid_type].add((nx, ny))

        target[fluid_type].add((x, y))

    def update(self, current_time):
        for fluid in self.FLUID_PROPERTIES.keys():
            fluid_data = self.FLUID_PROPERTIES[fluid]
            if current_time - fluid_data["last_update_time"] >= fluid_data["update_delay"]:
                fluid_data["last_update_time"] = current_time

                self.update_fluids(fluid)

    def update_fluids(self, fluid_type: str):
        """通用流體更新入口"""
        # 1. 清空下一幀的活躍清單
        self.next_active_fluids[fluid_type].clear()

        # 2. 統一遍歷當前所有活躍的該種流體
        for x, y in list(self.active_fluids[fluid_type]):

            level = self._get_fluid_level(fluid_type, x, y)
            if level is None:
                continue

            fluid_data = self.FLUID_PROPERTIES[fluid_type]

            if fluid_type == "water":
                self._update_single_water(x, y, fluid_data)
            elif fluid_type == "lava":
                self._update_single_lava(x, y, fluid_data)

        # 3. 統一更新當前活躍清單（只更新該流體的 Set）
        self.active_fluids[fluid_type] = self.next_active_fluids[fluid_type].copy()

    def _update_single_water(self, x: int, y: int, fluid_data):
        next_fluid = self.next_active_fluids["water"]

        # Step1: 取得目前水的等級
        level = self._get_fluid_level("water", x, y)

        has_changed = False

        # Step2: 向下流
        below = self._get_block(x, y + 1)
        below_level = self._get_fluid_level("water", x, y + 1)

        # print("[DEBUG](fluid_manager): Step2")
        if self._has_support("water", x, y):
            if below == "air":
                self._set_block(x, y + 1, "water_flow")
                next_fluid.add((x, y + 1))
                next_fluid.add((x, y))
                return

            if below_level is not None and below_level > level:
                self._set_block(x, y + 1, "water_flow")  # 用強水位覆蓋掉地下的弱水
                next_fluid.add((x, y + 1))
                has_changed = True
                # 注意：這裡不要 return！讓它繼續往下走 Step 3，向左右擴散開來！

        # Step3: 判斷能不能左右流
        new_level = level + 1

        # 只有當水位還沒達到最大值時，才能繼續向左右擴散
        # print("[DEBUG](fluid_manager): Step3")
        if self._has_support("water", x, y) and new_level <= fluid_data["max_level"]:
            for dx in (-1, 1):
                nx = x + dx
                side_block = self._get_block(nx, y)

                # 情況 A：旁邊是空氣才能流過去
                if self._is_air(side_block) and not self._is_fluid_type(below, "water"):
                    self._set_fluid("water", nx, y, new_level, dx)
                    next_fluid.add((nx, y))

                    has_changed = True

                # 情況 B：旁邊已經有水，且水位比我弱（數字大）-> 直接覆蓋！
                # (這裡不需要管 side_below，因為旁邊本來就有水了)
                elif self._is_fluid_type(side_block, "water"):
                    side_level = self._get_fluid_level("water", nx, y)
                    if side_level is not None and side_level > new_level:
                        self._set_fluid("water", nx, y, new_level, dx)
                        next_fluid.add((nx, y))

                        has_changed = True

        if has_changed:
            next_fluid.add((x, y))

        # Strp4: 檢查哪些水已經沒有來源
        # print("[DEBUG](fluid_manager): Step4")
        if not self._has_support("water", x, y):
            current_level = self._get_fluid_level("water", x, y)

            # 如果是瀑布或已經是最低水位，直接變空氣
            """降一級版本(非原版設定)"""
            # if current_level is None or current_level >= fluid_data["max_level"] or self._get_block(x, y) == "water_flow":
            #     self._set_block(x, y, "air")
            # else:
            #     # 降級：水位變弱一階（例如 water_1 變成 water_2）
            #     next_level = current_level + 1
            #     # 保持原本的方向 dir (根據檔名是否有 _rev)
            #     direction = 1 if "_rev" in self._get_block(x, y) else -1
            #     self._set_fluid("water", x, y, next_level, direction)
            """直接不見版"""
            if current_level is None or current_level >= fluid_data["max_level"] or self._is_fluid_type(self._get_block(x, y), "water"):
                self._set_block(x, y, "air")

            # # 喚醒四周，讓退潮效應像骨牌一樣向外傳遞
            self.wake_fluid("water", x, y, target=self.next_active_fluids)
            return

        # current_fluid.add((x, y))

    def _update_single_lava(self, x: int, y: int, fluid_data):
        pass

    # 內部 Helper：
    def _get_fluid_level(self, fluid_type: str, world_x: int, world_y: int):
        block = self._get_block(world_x, world_y)
        if block is None:
            return

        if self._is_fluid_type(block, fluid_type):
            return self._parse_fluid(block, fluid_type)

    def _get_fluid_direction(self, fluid_type, world_x: int, world_y: int):
        block = self._get_block(world_x, world_y)
        if block is None:
            return None

        if not self._is_fluid_type(block, fluid_type):
            return None

        if block in self.all_fluid_blocks:
            return 0

        if block.endswith("_rev"):
            return 1
        return -1

    def _set_fluid(
        self,
        fluid_type: str,
        x: int,
        y: int,
        level: int,
        dir: int = -1,
    ):
        """dir 要填 -1 或 1"""

        clamped_level = tool.clamp(0, self.FLUID_PROPERTIES[fluid_type]["max_level"], level)

        self._set_block(x, y, self._make_fluid(fluid_type, clamped_level, dir))

    def _get_block(self, world_x: int, world_y: int) -> str | None:
        chunk_x = world_x // config.CHUNK_WIDTH
        local_x = world_x % config.CHUNK_WIDTH

        if chunk_x in self.chunks and 0 <= world_y < config.MAP_HEIGHT:
            return self.chunks[chunk_x].blocks[world_y][local_x]
        return None

    def _set_block(self, world_x: int, world_y: int, block_type: str):
        chunk_x = world_x // config.CHUNK_WIDTH
        local_x = world_x % config.CHUNK_WIDTH

        if chunk_x in self.chunks and 0 <= world_y < config.MAP_HEIGHT:
            self.chunks[chunk_x].blocks[world_y][local_x] = block_type
            self.chunks[chunk_x].is_dirty = True

    def _make_fluid(self, fluid_type: str, level: int, dir: int = 0):
        if dir == 0:
            return f"{fluid_type}_source"
        elif dir == -1:
            return f"{fluid_type}_{level}"
        elif dir == 1:
            return f"{fluid_type}_{level}_rev"

    def _parse_fluid(self, block: str, fluid_type: str):
        if not self._is_fluid_type(block, fluid_type):
            return None

        if block == f"{fluid_type}_flow":
            return 1

        if block == f"{fluid_type}_source":
            return 0

        clean_block = block.replace("_rev", "")
        parts = clean_block.split("_")

        if len(parts) != 2:
            return None

        return int(parts[1])

    def _neighbors(self, x: int, y: int):
        return [
            (x, y - 1),
            (x, y + 1),
            (x - 1, y),
            (x + 1, y),
        ]

    """判斷"""

    def is_fluid(self, block: str):
        if block is None:
            return False
        return any(block.startswith(fluid) for fluid in self.FLUID_PROPERTIES)

    def _is_fluid_type(self, block: str, fluid_type):
        if block is None:
            return False
        return block.startswith(fluid_type)

    def _is_air(self, block):
        return block == "air"

    def _is_solid(self, block):
        return block is not None and block != "air" and not self.is_fluid(block)

    def _has_support(self, fluid_type: str, x: int, y: int):
        self_level = self._get_fluid_level(fluid_type, x, y)
        if self_level is None:
            return False

        if self_level == 0:
            return True

        above = self._get_fluid_level(fluid_type, x, y - 1)
        above_block = self._get_block(x, y - 1)

        if self._get_block(x, y) == f"{fluid_type}_flow":
            if above_block is not None and self._is_fluid_type(above_block, fluid_type):
                return True
            return False

        if above is not None and above <= self_level:
            return True

        # 左右必須是比自己強一級的水
        left = self._get_fluid_level(fluid_type, x - 1, y)
        left_dir = self._get_fluid_direction(fluid_type, x - 1, y)
        # left_block = self._get_block(x - 1, y)
        if left is not None:
            if (left_dir == 0) or (left_dir == 1 and left <= self_level - 1):
                return True

        right = self._get_fluid_level(fluid_type, x + 1, y)
        right_dir = self._get_fluid_direction(fluid_type, x + 1, y)
        # right_block = self._get_block(x + 1, y)
        if right is not None:
            if right_dir == 0 or (right_dir == -1 and right <= self_level - 1):
                return True

        return False
