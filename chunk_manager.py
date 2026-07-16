import math
import os
import random

import opensimplex

import config
import save_manager
import tool

save = save_manager.SaveManager()

world_dir = config.BASE_DIR / "saves" / config.CURRENT_WORLD / "chunks"
info_dir = config.BASE_DIR / "saves" / config.CURRENT_WORLD

if not os.path.exists(world_dir):
    os.makedirs(world_dir, exist_ok=True)
if not os.path.exists(info_dir):
    os.makedirs(info_dir, exist_ok=True)


class Chunk:
    def __init__(self, chunk_x: int, blocks):
        self.chunk_x = chunk_x
        self.blocks = blocks
        self.is_dirty = False


def get_block(x_pos, y_pos):
    world_grid_x = x_pos // config.BLOCK_SIZE

    chunk_index = world_grid_x // config.CHUNK_WIDTH

    local_x = world_grid_x % config.CHUNK_WIDTH
    local_y = y_pos // config.BLOCK_SIZE

    chunk = get_chunk(chunk_index)

    return chunk.blocks[local_y][local_x]


def set_block(world_x, world_y, block_type):
    # 1. 根據世界格子 X 座標，算出在哪一個 Chunk 區塊
    chunk_i = world_x // config.CHUNK_WIDTH

    # 2. 如果該區塊剛好還沒生成，就先把它生出來
    if chunk_i not in config.chunks:
        get_chunk(chunk_i)

    # 3. 換算出在該區塊內（0 ~ 15）的相對 X 座標
    chunk_x = world_x % config.CHUNK_WIDTH
    chunk_y = world_y  # Y 軸是固定的垂直高度，不需要取餘數

    # 4. 寫入方塊（記得照你 make_map 的順序先 Y 後 X）
    chunk = get_chunk(chunk_i)

    chunk.blocks[chunk_y][chunk_x] = block_type
    chunk.is_dirty = True


def get_chunk(chunk_x) -> Chunk:
    # 1. 已經載入
    if chunk_x in config.chunks:
        return config.chunks[chunk_x]

    # 2. 嘗試讀取存檔
    loaded_chunk = save.load_chunk(chunk_x)

    if loaded_chunk is not None:
        config.chunks[chunk_x] = Chunk(chunk_x, loaded_chunk)
        return config.chunks[chunk_x]

    # 3. 沒有存檔就生成
    chunk = Chunk(
        chunk_x,
        make_map(config.CHUNK_WIDTH, config.MAP_HEIGHT, chunk_x)
    )

    config.chunks[chunk_x] = chunk
    return chunk


def make_map(map_width, map_height, current_chunk_i):
    chunk_data = []
    height_map = _make_terrain(current_chunk_i)
    dirt_depth_map = [random.randint(3, 5) for _ in range(map_width)]
    rock_depth_map = [random.randint(int(config.MAP_HEIGHT // 2.5) - 5, int(config.MAP_HEIGHT // 2.5) + 5) for _ in range(map_width)]

    # 橫向一列一列由上往下生成
    for y in range(map_height):
        row = []
        for x in range(map_width):
            target_y = height_map[x]
            dirt_depth = dirt_depth_map[x]
            dirt_end_y = target_y + dirt_depth
            # 根據 y 的位置（深度）來決定方塊種類
            if y < target_y:
                block = "air"  # 最上面 10 格是天空
            elif y == config.MAP_HEIGHT - 1:
                block = "bedrock"
            elif y == target_y:
                block = "grass"  # 第 10 格是表面草地
            elif target_y < y < dirt_end_y:
                block = "dirt"  # 再往下 4 格是泥土
            elif y < dirt_end_y + rock_depth_map[x]:
                block = "stone"
            elif y < config.MAP_HEIGHT:
                block = "deepslate"

            row.append(block)
        chunk_data.append(row)

    chunk_data = _generate_veins(chunk_data, map_width, map_height)
    # chunk_data = _generate_veins(chunk_data, map_width, map_height)

    return chunk_data


def _make_terrain(chunk_x):
    config.height_map = []

    # 💡 提示：設定一個隨機種子，讓每次地形都不一樣
    opensimplex.seed(config.WORLD_SEED)

    baseline = 25  # 地平線基準面

    for local_x in range(config.CHUNK_WIDTH):
        world_x = chunk_x * config.CHUNK_WIDTH + local_x

        raw_noise = opensimplex.noise2(world_x / 30.0, 0)

        # 2. ✨ 關鍵：取 3 次方！這會讓接近 0 的地方大面積變平平的
        # math.copysign 是為了保留原本的正負號（讓它有山也有谷）
        flattened_noise = math.copysign(abs(raw_noise) ** 2.5, raw_noise)

        # 3. 乘以山的高度落差
        noise_val = flattened_noise * 22.0

        current_height = baseline + int(noise_val)

        # 安全防護，防止方塊超出地圖
        current_height = tool.clamp(5, config.MAP_HEIGHT - 5, current_height)
        config.height_map.append(current_height)

    return config.height_map


def _generate_veins(chunk_data, map_width, map_height):

    # 🛠️ 在這裡集中管理所有礦物的生成規則，要新增礦物只要在這邊加一行就好！
    ore_rules = [
        # {"name": 礦物名稱, "min_y": 最高高度, "max_y": 最低高度, "veins_range": 群落數範圍, "size_range": 每坨大小, "target_stones": 能替換的石頭}
        {"name": "iron_ore", "min_y": 15, "max_y": 73, "veins_range": (1, 3), "size_range": (5, 18), "target_stones": ["stone"]},
        {"name": "coal_ore", "min_y": 15, "max_y": 73, "veins_range": (1, 3), "size_range": (5, 25), "target_stones": ["stone"]},
        {"name": "copper_ore", "min_y": 15, "max_y": 65, "veins_range": (1, 3), "size_range": (4, 8), "target_stones": ["stone"]},
        {"name": "gold_ore", "min_y": 20, "max_y": 73, "veins_range": (1, 3), "size_range": (1, 6), "target_stones": ["stone"]},
        {"name": "diamond_ore", "min_y": 40, "max_y": 73, "veins_range": (1, 1), "size_range": (1, 6), "target_stones": ["stone"]},
        {"name": "redstone_ore", "min_y": 25, "max_y": 58, "veins_range": (2, 5), "size_range": (1, 6), "target_stones": ["stone"]},
        {"name": "lapis_ore", "min_y": 40, "max_y": 58, "veins_range": (3, 7), "size_range": (2, 8), "target_stones": ["stone"]},
        {
            "name": "deepslate_iron_ore",
            "min_y": 60,
            "max_y": 135,
            "veins_range": (1, 3),
            "size_range": (5, 18),
            "target_stones": ["deepslate"],
        },
        {
            "name": "deepslate_coal_ore",
            "min_y": 60,
            "max_y": 135,
            "veins_range": (1, 3),
            "size_range": (5, 20),
            "target_stones": ["deepslate"],
        },
        {
            "name": "deepslate_emerald_ore",
            "min_y": 80,
            "max_y": 135,
            "veins_range": (1, 3),
            "size_range": (1, 1),
            "target_stones": ["deepslate"],
        },
        {
            "name": "deepslate_diamond_ore",
            "min_y": 60,
            "max_y": 135,
            "veins_range": (1, 3),
            "size_range": (1, 6),
            "target_stones": ["deepslate"],
        },
        {
            "name": "deepslate_redstone_ore",
            "min_y": 60,
            "max_y": 119,
            "veins_range": (2, 5),
            "size_range": (1, 6),
            "target_stones": ["deepslate"],
        },
        {
            "name": "deepslate_lapis_ore",
            "min_y": 60,
            "max_y": 119,
            "veins_range": (3, 7),
            "size_range": (2, 8),
            "target_stones": ["deepslate"],
        },
    ]

    # ✨ 核心魔法：用一個迴圈，把所有礦物的規則依序拿出來跑
    for rule in ore_rules:
        num_of_veins = random.randint(rule["veins_range"][0], rule["veins_range"][1])
        for _ in range(num_of_veins):
            attempts = 0
            max_attempts = 30
            while attempts < max_attempts:
                attempts += 1
                # 🎯 修正：這樣 center_x 就會乖乖在 0 ~ 15 格之間隨機分散了
                center_x = random.randint(0, map_width - 1)
                center_y = random.randint(rule["min_y"], rule["max_y"])
                if chunk_data[center_y][center_x] in rule["target_stones"]:
                    break

            vein_size = random.randint(rule["size_range"][0], rule["size_range"][1])
            # 🎯 修正：傳入 map_width
            _veins_spawn(chunk_data, vein_size, center_y, center_x, map_width, map_height, rule["name"])

    return chunk_data


def _veins_spawn(chunk_data, vein_size, center_y, center_x, map_width, map_height, vein_name):
    blocks_placed = 0

    # 建立一個「已經被感染」的方塊坐標清單，起點是中心
    # 使用 set 是為了方便快速判斷某格是不是已經變成鐵礦了
    infected_blocks = set()
    infected_blocks.add((center_x, center_y))

    # 先把中心點放下去
    if chunk_data[center_y][center_x] in ["stone", "deepslate"]:
        chunk_data[center_y][center_x] = vein_name
        blocks_placed += 1

    # 🎯 建立一個安全計數器，防止無限迴圈
    attempts = 0
    max_attempts = vein_size * 5

    # 用 while 確保一定要放滿指定格數
    while blocks_placed < vein_size and attempts < max_attempts:
        attempts += 1

        base_x, base_y = random.choice(list(infected_blocks))

        # 從這個挑選到的「突觸點」隨機抽一個上下左右的方向
        dx, dy = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
        next_x = max(0, min(map_width - 1, base_x + dx))
        next_y = max(0, min(map_height - 1, base_y + dy))

        # 如果下一個位置是石頭，且還沒被感染
        if chunk_data[next_y][next_x] in ["stone", "deepslate"] and (next_x, next_y) not in infected_blocks:
            # 放下礦石
            chunk_data[next_y][next_x] = vein_name
            # 把這格加入「被感染清單」，下次也可能從這格突觸
            infected_blocks.add((next_x, next_y))
            blocks_placed += 1
