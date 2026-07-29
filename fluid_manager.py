import config

"""
今天我改了哪些地方？

1.active_fluids → next_active_fluids
2.add_fluid() 改過
3.wake_water() 改過
4.新增 _has_support()
5.新增 _get_water_direction()
6.把 Step4 加進 update_fluids()
7.water_source 放置時呼叫 add_fluid()

其中 最值得懷疑的是 4、5、6。
"""


class FluidManager:
    def __init__(self, chunks):
        self.chunks = chunks

        self.active_fluids = set()
        self.next_active_fluids = set()

        self.fluid_update_interval = 300  # 水流每次更新時間
        self.last_fluid_update_time = 0

        self.MAX_WATER_LEVEL = 8

    def add_fluid(self, world_x: int, world_y: int):
        """當玩家放置水，或是地圖生成水源時呼叫此方法"""
        self.active_fluids.add((world_x, world_y))

    def wake_water(self, x, y, target=None):
        if target is None:
            target = self.active_fluids

        for nx, ny in self._neighbors(x, y):
            target.add((nx, ny))

        target.add((x, y))

    def update(self, current_time):
        if current_time - self.last_fluid_update_time >= self.fluid_update_interval:
            self.update_fluids()
            self.last_fluid_update_time = current_time

    def update_fluids(self):
        """重要：如果左右已經有水，而且它的水位比我還要高，就更新它。"""

        self.next_active_fluids.clear()

        # 遍歷所有活躍水
        for x, y in list(self.active_fluids):

            # Step1: 取得目前水的等級
            level = self._get_water_level(x, y)

            if level is None:
                continue

            # Step2: 向下流
            below = self._get_block(x, y + 1)
            below_level = self._get_water_level(x, y + 1)

            if self._has_support(x, y):
                if below == "air":
                    self._set_block(x, y + 1, "water_flow")
                    self.next_active_fluids.add((x, y + 1))
                    continue

                if below_level is not None and below_level > level:
                    self._set_block(x, y + 1, "water_flow")  # 用強水位覆蓋掉地下的弱水
                    self.next_active_fluids.add((x, y + 1))
                    # 注意：這裡不要 continue！讓它繼續往下走 Step 3，向左右擴散開來！

            # Step3: 判斷能不能左右流
            new_level = level + 1

            # 只有當水位還沒達到最大值時，才能繼續向左右擴散
            if self._has_support(x, y) and new_level <= self.MAX_WATER_LEVEL:
                for dx in (-1, 1):
                    nx = x + dx
                    side_block = self._get_block(nx, y)
                    # side_below = self._get_block(nx, y + 1)  # 👈 取得目標位置的下方方塊

                    # 情況 A：旁邊是空氣才能流過去
                    if self._is_air(side_block) and not self.is_water(below):  #  and self._is_solid(side_below)
                        self._set_water(nx, y, new_level, dx)
                        self.next_active_fluids.add((nx, y))

                    # 情況 B：旁邊已經有水，且水位比我弱（數字大）-> 直接覆蓋！
                    # (這裡不需要管 side_below，因為旁邊本來就有水了)
                    elif self.is_water(side_block):
                        side_level = self._get_water_level(nx, y)
                        if side_level is not None and side_level > new_level:
                            self._set_water(nx, y, new_level, dx)
                            self.next_active_fluids.add((nx, y))

            if level is not None:
                self.next_active_fluids.add((x, y))

            # Strp4: 檢查哪些水已經沒有來源
            if not self._has_support(x, y):
                current_level = self._get_water_level(x, y)

                # 如果是瀑布或已經是最低水位，直接變空氣
                if current_level is None or current_level >= self.MAX_WATER_LEVEL or self._get_block(x, y) == "water_flow":
                    self._set_block(x, y, "air")
                else:
                    # 降級：水位變弱一階（例如 water_1 變成 water_2）
                    next_level = current_level + 1
                    # 保持原本的方向 dir (根據檔名是否有 _rev)
                    direction = 1 if "_rev" in self._get_block(x, y) else -1
                    self._set_water(x, y, next_level, direction)

                # 喚醒四周，讓退潮效應像骨牌一樣向外傳遞
                self.wake_water(x, y, target=self.next_active_fluids)
                # self.next_active_fluids.add((x, y))
                continue

        self.active_fluids = self.next_active_fluids.copy()

    # 內部 Helper：
    def _get_water_level(self, world_x: int, world_y: int):
        block = self._get_block(world_x, world_y)
        if block is None:
            return

        if self.is_water(block):
            return self._parse_water(block)

    def _get_water_direction(self, world_x: int, world_y: int):
        block = self._get_block(world_x, world_y)
        if block is None:
            return None

        if not self.is_water(block):
            return None

        if block in ["water_flow", "water_source"]:
            return 0

        if block.endswith("_rev"):
            return 1
        return -1

    def _set_water(self, x: int, y: int, level: int, dir: int = -1):
        """dir 要填 -1 或 1"""

        if level > self.MAX_WATER_LEVEL:
            level = self.MAX_WATER_LEVEL

        self._set_block(x, y, self._make_water(level, dir))

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

    def _make_water(self, level: int, dir: int = 0):
        if dir == 0:
            return "water_source"
        elif dir == -1:
            return f"water_{level}"
        elif dir == 1:
            return f"water_{level}_rev"

    def _parse_water(self, block: str):
        if not self.is_water(block):
            return None

        if block == "water_flow":
            return 1

        if block == "water_source":
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

    def is_water(self, block: str):
        if block is None:
            return False
        return block.startswith("water")

    def _is_air(self, block):
        return block == "air"

    def _is_solid(self, block):
        return block is not None and block != "air" and not self.is_water(block)

    def _has_support(self, x, y):
        self_level = self._get_water_level(x, y)
        if self_level is None:
            return False

        if self_level == 0:
            return True

        above = self._get_water_level(x, y - 1)
        above_block = self._get_block(x, y - 1)

        if self._get_block(x, y) == "water_flow":
            if above_block is not None and self.is_water(above_block):
                return True
            return False

        if above is not None and above <= self_level:
            return True

        # 左右必須是比自己強一級的水
        left = self._get_water_level(x - 1, y)
        left_dir = self._get_water_direction(x - 1, y)
        # left_block = self._get_block(x - 1, y)
        if left is not None:
            if (left_dir == 0) or (left_dir == 1 and left <= self_level - 1):
                return True

        right = self._get_water_level(x + 1, y)
        right_dir = self._get_water_direction(x + 1, y)
        # right_block = self._get_block(x + 1, y)
        if right is not None:
            if right_dir == 0 or (right_dir == -1 and right <= self_level - 1):
                return True

        return False
