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


# 之後加"grass_color": (70,180,70),
BIOMES = {
    "plains": {
        "name": "plains",
        "surface": "grass",
        "dirt": "dirt",
        "tree": "oak",
        "tree_rate": 0.03,
        "height": 8,
        "chunk_size": (4, 7),
    },
    "forest": {
        "name": "forest",
        "surface": "grass",
        "dirt": "dirt",
        "tree": "oak",
        "tree_rate": 0.15,
        "height": 12,
        "chunk_size": (3, 6),
    },
    "birch_forest": {
        "name": "birch_forest",
        "surface": "grass",
        "dirt": "dirt",
        "tree": "birch",
        "tree_rate": 0.15,
        "height": 12,
        "chunk_size": (3, 6),
    },
    "desert": {
        "name": "desert",
        "surface": "sand",
        "dirt": "sand",
        "tree": None,
        "tree_rate": 0,
        "height": 5,
        "chunk_size": (5, 9),
    },
    "mountain": {
        "name": "mountain",
        "surface": "grass",
        "dirt": "dirt",
        "tree": "spruce",
        "tree_rate": 0.02,
        "height": 35,
        "chunk_size": (3, 7),
    },
    "stone_mountain": {
        "name": "stone_mountain",
        "surface": "stone",
        "dirt": "stone",
        "tree": "spruce",
        "tree_rate": 0.02,
        "height": 35,
        "chunk_size": (3, 7),
    },
    "snow": {
        "name": "snow",
        "surface": "grass",
        "surface_cover": "snow",
        "dirt": "dirt",
        "tree": "spruce",
        "tree_rate": 0.05,
        "height": 10,
        "chunk_size": (5, 8),
    },
    "snow_forest": {
        "name": "snow_forest",
        "surface": "grass",
        "surface_cover": "snow",
        "dirt": "dirt",
        "tree": "spruce",
        "tree_rate": 0.15,
        "height": 10,
        "chunk_size": (4, 7),
    },
    "jungle": {
        "name": "jungle",
        "surface": "grass",
        "dirt": "dirt",
        "tree": "jungle",
        "tree_rate": 0.25,
        "height": 15,
        "chunk_size": (3, 6),
    },
    # "volcano": {
    #     "name": "volcano",
    #     "surface": "basalt_side",
    #     "dirt": "stone",
    #     "tree": None,
    #     "tree_rate": 0,
    #     "height": 45,
    #     "chunk_size": (3, 7),
    # },
}

TREES = {
    "oak": {
        "height": (4, 6),
        "shape": "oak",
    },
    "birch": {
        "height": (5, 7),
        "shape": "birch",
    },
    "spruce": {
        "height": (7, 10),
        "shape": "spruce",
    },
    "jungle": {
        "height": (9, 15),
        "shape": "jungle",
    },
}


class Chunk:
    def __init__(self, chunk_x: int, blocks, biome_name):
        self.chunk_x = chunk_x
        self.blocks = blocks
        self.is_dirty = False
        self.biome_name = biome_name
        # self.rng = random.Random(config.WORLD_SEED + chunk_x * 1000003)


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
    rng = random.Random(config.WORLD_SEED)

    if loaded_chunk is not None:
        biome_name = _generate_biome(chunk_x, rng)

        config.chunks[chunk_x] = Chunk(chunk_x, loaded_chunk, biome_name)
        return config.chunks[chunk_x]

    # 3. 沒有存檔就生成
    blocks, biome_name = make_map(config.CHUNK_WIDTH, config.MAP_HEIGHT, chunk_x)

    chunk = Chunk(chunk_x, blocks, biome_name)

    config.chunks[chunk_x] = chunk
    return chunk


def make_map(map_width, map_height, current_chunk_i):
    chunk_data = []
    rng = random.Random(config.WORLD_SEED + current_chunk_i * 1000003)

    biome_name = _generate_biome(current_chunk_i, rng)
    # print(current_chunk_i, biome_name)

    height_map = _make_terrain(current_chunk_i)

    chunk_data = _make_base_terrain(map_width, map_height, current_chunk_i, biome_name, height_map, rng)
    chunk_data = _generate_caves(current_chunk_i, chunk_data, height_map)
    chunk_data = _generate_cave_entrances(current_chunk_i, chunk_data, height_map, rng)
    chunk_data = _generate_trees(current_chunk_i, biome_name, chunk_data, height_map, rng)
    chunk_data = _cleanup_terrain(current_chunk_i, chunk_data, height_map)
    chunk_data = _generate_underground_water(current_chunk_i, chunk_data, height_map)
    chunk_data = _generate_veins(chunk_data, map_width, map_height, rng)

    return chunk_data, biome_name


biome_list = []

last_chunk = 0


def _generate_biome(chunk_x, rng: random.Random):
    if not biome_list:
        biome = rng.choice(list(BIOMES.keys()))
        length = rng.randint(*BIOMES[biome]["chunk_size"])

        biome_list.append({"start": 0, "end": length, "biome": biome})

    while chunk_x >= biome_list[-1]["end"]:
        start = biome_list[-1]["end"]

        biome = rng.choice(list(BIOMES.keys()))
        while biome == biome_list[-1]["biome"]:
            biome = rng.choice(list(BIOMES.keys()))

        length = rng.randint(*BIOMES[biome]["chunk_size"])

        biome_list.append({"start": start, "end": start + length, "biome": biome})
    while chunk_x < biome_list[0]["start"]:

        end = biome_list[0]["start"]

        biome = rng.choice(list(BIOMES.keys()))

        while biome == biome_list[0]["biome"]:
            biome = rng.choice(list(BIOMES.keys()))

        length = rng.randint(*BIOMES[biome]["chunk_size"])

        biome_list.insert(0, {"start": end - length, "end": end, "biome": biome})

    return _get_biome(biome_list, chunk_x)


def _get_biome(biome_list, chunk_x):
    for biome in biome_list:
        if biome["start"] <= chunk_x < biome["end"]:
            return biome["biome"]


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


def _make_base_terrain(map_width, map_height, chunk_x, biome_name, height_map, rng: random.Random):
    chunk_data = []

    dirt_depth_map = [rng.randint(3, 5) for _ in range(map_width)]

    for y in range(map_height):
        row = []
        for x in range(map_width):
            target_y = height_map[x]
            biome = BIOMES[biome_name]
            dirt_end_y = target_y + dirt_depth_map[x]

            world_x = chunk_x * config.CHUNK_WIDTH + x

            offset = opensimplex.noise2(world_x / 80, 500) * 5
            stone_limit = int(config.MAP_HEIGHT * 0.4 + offset)

            if y < target_y:
                block = "air"
            elif y == config.MAP_HEIGHT - 1:
                block = "bedrock"
            elif y == target_y:
                block = biome["surface"]
            elif target_y < y < dirt_end_y:
                block = biome["dirt"]
            elif y < stone_limit:
                block = "stone"
            elif y < config.MAP_HEIGHT:
                block = "deepslate"

            row.append(block)
        chunk_data.append(row)

    return chunk_data


def _generate_caves(chunk_x, chunk_data, height_map):
    for local_x in range(config.CHUNK_WIDTH):
        world_x = chunk_x * config.CHUNK_WIDTH + local_x

        cave_depth_noise = opensimplex.noise2(world_x / 150, 300)

        value = (cave_depth_noise + 1) / 2
        dynamic_buffer = int((1 - value) * 7)

        # 取得這一行的高度限制（之前 _make_terrain 算出來的）
        surface_height = height_map[local_x]

        for y in range(config.MAP_HEIGHT):
            # 主洞窟
            cave_noise = opensimplex.noise2(world_x / 20.0, y / 20.0)
            # 控制洞大小(門檻)
            size_noise = opensimplex.noise2(world_x / 120, y / 120)

            room_noise = opensimplex.noise2(world_x / 80, y / 120)
            tunnel_noise = opensimplex.noise2(world_x / 12, y / 12)
            # 粗糙
            # rough_noise = opensimplex.noise2(world_x / 4, y / 4)
            # 地下湖

            base_threshold = 0.4
            threshold = base_threshold + size_noise * 0.12

            if chunk_data[y][local_x] == "bedrock":
                continue

            density = cave_noise

            if room_noise > 0.6:
                density += 0.35

            if tunnel_noise > 0.6:
                density += 0.2

            underground = y > surface_height + dynamic_buffer and density > threshold
            if not underground:
                continue

            lake_noise = opensimplex.noise2(world_x / 120, y / 120)
            # lava_noise = opensimplex.noise2(world_x / 120, y / 120)

            if lake_noise > 0.72 and y > 80:
                chunk_data[y][local_x] = "water_still"
            else:
                chunk_data[y][local_x] = "air"

    return chunk_data


def _generate_cave_entrances(chunk_x, chunk_data, height_map, rng: random.Random):
    for local_x in range(config.CHUNK_WIDTH):

        world_x = chunk_x * config.CHUNK_WIDTH + local_x

        # 不是每個地方都生成入口
        noise = opensimplex.noise2(world_x / 120, 999)
        right_noise = opensimplex.noise2((world_x + 1) / 120, 999)
        left_noise = opensimplex.noise2((world_x - 1) / 120, 999)
        if not (noise >= left_noise and noise >= right_noise):
            continue

        surface_y = height_map[local_x]

        # 找最近的洞窟
        cave_y = None
        for y in range(surface_y + 5, min(surface_y + 50, config.MAP_HEIGHT - 3)):
            if chunk_data[y][local_x] == "air" and chunk_data[y + 1][local_x] == "air" and chunk_data[y + 2][local_x] == "air":
                cave_y = y
                break

        if cave_y is None:
            continue

        shaft_x = local_x
        radius = rng.randint(1, rng.randint(2, 5))

        for yy in range(surface_y - 1, cave_y + 1):

            # 每隔幾格稍微偏移
            bend_step = rng.randint(3, 6)
            radius_step = rng.randint(4, 7)
            if yy % bend_step == 0:
                shaft_x += rng.choice([-1, 0, 1])
                shaft_x = max(radius, min(config.CHUNK_WIDTH - radius - 1, shaft_x))
                if yy % radius_step == 0:
                    radius = tool.clamp(1, 5, radius - rng.choice([0, 1]))

            # 挖圓形，不要方形
            for xx in range(shaft_x - radius, shaft_x + radius + 1):
                if not (0 <= xx < config.CHUNK_WIDTH):
                    continue

                if (xx - shaft_x) ** 2 <= radius**2:
                    chunk_data[yy][xx] = "air"
    return chunk_data


def _cleanup_terrain(chunk_x, chunk_data, height_map):
    new_chunk = [row[:] for row in chunk_data]

    # stone_neighbors = 0
    for local_x in range(config.CHUNK_WIDTH):
        for y in range(config.MAP_HEIGHT):
            # 第一種：清理單獨的小方塊
            air_blocks = 0
            for xx in range(local_x - 1, local_x + 2):
                for yy in range(y - 1, y + 2):
                    if xx == local_x and yy == y:
                        continue

                    if xx < 0 or xx >= config.CHUNK_WIDTH:
                        continue
                    if yy < 0 or yy >= config.MAP_HEIGHT:
                        continue

                    if chunk_data[yy][xx] == "air":
                        air_blocks += 1
            if chunk_data[y][local_x] != "air":
                if air_blocks >= 7:
                    new_chunk[y][local_x] = "air"

            # 第二種：填掉單獨的小洞
            solid_count = 0
            solid_type = ""
            for xx in range(local_x - 1, local_x + 2):
                for yy in range(y - 1, y + 2):
                    if xx == local_x and yy == y:
                        continue

                    if xx < 0 or xx >= config.CHUNK_WIDTH:
                        continue
                    if yy < 0 or yy >= config.MAP_HEIGHT:
                        continue

                    if chunk_data[yy][xx] != "air":
                        solid_count += 1
                        solid_type = chunk_data[yy][xx]

            if chunk_data[y][local_x] != "air":
                if solid_count >= 8:
                    new_chunk[y][local_x] = solid_type

            # if stone_neighbors >= 5:
            #     chunk_data[y][local_x] = "stone"

            # if stone_neighbors < 5:
            #     chunk_data[y][local_x] = "air"
    return new_chunk


def _generate_underground_water(chunk_x, chunk_data, height_map):
    for local_x in range(config.CHUNK_WIDTH):
        world_x = chunk_x * config.CHUNK_WIDTH + local_x
        surface_y = height_map[local_x]

        # 限制地下水只在特定深度生成（例如：地表下方 15 格開始，到 Y = 95 之間）
        min_water_y = surface_y + 15
        max_water_y = 95
        for y in range(config.MAP_HEIGHT):
            if y >= config.MAP_HEIGHT or y >= max_water_y or y <= min_water_y:
                continue

            if chunk_data[y][local_x] == "bedrock":
                continue

            # 1. 大範圍的主水脈形狀 Noise (頻率稍微拉大，讓水脈看起來比較粗、比較連貫)
            water_vein_noise = opensimplex.noise2(world_x / 35.0, y / 20.0)

            # 2. 地下水位控制 Noise (用來模擬起伏的地下水位線)
            water_table_noise = opensimplex.noise2(world_x / 80.0, 0)

            # 換算出動態的水位門檻（例如值越大，水位越高）
            depth_factor = (y - min_water_y) / (max_water_y - min_water_y)  # 算出一個 0~1 的深度比例
            water_threshold = 0.75 - (depth_factor * 0.3) + (water_table_noise * 0.1)

            if water_vein_noise > water_threshold:
                # 為了好玩，只有當這一格目前是空氣(洞窟)、泥土或石頭時，才把它填成水
                # 這樣有些原本被挖空的洞窟，下半段就會淹水，變成漂亮的地下湖泊！
                current_block = chunk_data[y][local_x]
                if current_block in ["air", "dirt", "stone"]:
                    chunk_data[y][local_x] = "water_still"
    return chunk_data


def _generate_veins(chunk_data, map_width, map_height, rng: random.Random):

    # 🛠️ 在這裡集中管理所有礦物的生成規則，要新增礦物只要在這邊加一行就好！
    ore_rules = [
        # {"name": 礦物名稱, "min_y": 最高高度, "max_y": 最低高度, "veins_range": 群落數範圍, "size_range": 每坨大小, "target_stones": 能替換的石頭}
        {"name": "iron_ore", "min_y": 15, "max_y": 73, "veins_range": (1, 3), "size_range": (5, 18), "target_stones": ["stone"]},
        {"name": "coal_ore", "min_y": 15, "max_y": 73, "veins_range": (1, 3), "size_range": (5, 25), "target_stones": ["stone"]},
        {"name": "copper_ore", "min_y": 15, "max_y": 65, "veins_range": (1, 3), "size_range": (4, 8), "target_stones": ["stone"]},
        {"name": "gold_ore", "min_y": 20, "max_y": 73, "veins_range": (1, 3), "size_range": (1, 6), "target_stones": ["stone"]},
        {"name": "diamond_ore", "min_y": 40, "max_y": 73, "veins_range": (1, 1), "size_range": (1, 6), "target_stones": ["stone"]},
        {"name": "redstone_ore", "min_y": 25, "max_y": 58, "veins_range": (2, 4), "size_range": (1, 6), "target_stones": ["stone"]},
        {"name": "lapis_ore", "min_y": 40, "max_y": 58, "veins_range": (1, 4), "size_range": (2, 8), "target_stones": ["stone"]},
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
        num_of_veins = rng.randint(rule["veins_range"][0], rule["veins_range"][1])
        for _ in range(num_of_veins):
            attempts = 0
            max_attempts = 30
            while attempts < max_attempts:
                attempts += 1
                # 🎯 修正：這樣 center_x 就會乖乖在 0 ~ 15 格之間隨機分散了
                center_x = rng.randint(0, map_width - 1)
                center_y = rng.randint(rule["min_y"], rule["max_y"])
                if chunk_data[center_y][center_x] in rule["target_stones"]:
                    break

            vein_size = rng.randint(rule["size_range"][0], rule["size_range"][1])
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


"""
├── _draw_oak()
├── _draw_birch()
├── _draw_spruce()
├── _draw_jungle()
├── _draw_cherry()
└── _set_leaves_safe()
"""

TREE_PATTERNS = {
    "oak": {"height": (6, 8), "leaves": [[3, 3, 5, 5]]},  # [4, 6, 7, 9, 8, 7, 7, 2]  阿姆斯特朗炮，之後做
    "birch": {"height": (6, 8), "leaves": [[1, 3, 3, 5, 5]]},
    "spruce": {"height": (12, 15), "leaves": [[1, 3, 1, 3, 5, 3, 5, 3, 5], [1, 3, 3, 3]]},
    "jungle": {"height": (10, 16), "leaves": [[3, 3, 5, 5]]},
}


def _draw_tree(tree_type, plant_local_x, bottom_y, chunk_x, chunk_data, rng: random.Random):
    if tree_type not in TREE_PATTERNS:
        print(f"Unknown tree type: {tree_type}")
        return

    pattern = TREE_PATTERNS[tree_type]
    min_height, max_height = pattern["height"]
    tree_height = rng.randint(min_height, max_height)

    # 畫樹幹
    for y in range(bottom_y, bottom_y - tree_height, -1):
        if 0 <= y < config.MAP_HEIGHT:
            chunk_data[y][plant_local_x] = f"{tree_type}_log"

    # 畫樹冠
    top_y = bottom_y - tree_height + 1
    leaves_pattern = rng.choice(pattern["leaves"])

    for i, width in enumerate(leaves_pattern):
        leaf_y = top_y + i
        _place_leaf_rectangle(tree_type, plant_local_x, leaf_y, width, 1, chunk_x, chunk_data)


# def _draw_oak(plant_local_x, bottom_y, chunk_x, chunk_data, rng: random.Random):
#     # 1. 決定樹幹高度
#     tree_height = rng.randint(4, 6)
#     # 2. 畫樹幹 (直接寫入當前的 chunk_data，安全且快速)
#     for y in range(bottom_y, bottom_y - tree_height, -1):
#         if 0 <= y < config.MAP_HEIGHT:
#             chunk_data[y][plant_local_x] = "oak_log"

#     # 3. 畫樹冠
#     top_y = bottom_y - tree_height + 1

#     # 下半部 5 x 2 樹葉
#     _place_leaf_rectangle("oak", plant_local_x, top_y - 1, 5, 2, chunk_x, chunk_data)

#     # 上半部 3 x 2 樹葉
#     _place_leaf_rectangle("oak", plant_local_x, top_y - 3, 3, 2, chunk_x, chunk_data)


# def _draw_birch(plant_local_x, bottom_y, chunk_x, chunk_data):
#     # 1. 決定樹幹高度
#     tree_height = random.randint(6, 8)
#     # 2. 畫樹幹 (直接寫入當前的 chunk_data，安全且快速)
#     for y in range(bottom_y, bottom_y - tree_height, -1):
#         if 0 <= y < config.MAP_HEIGHT:
#             chunk_data[y][plant_local_x] = "birch_log"
#     top_y = bottom_y - tree_height + 1
#     _place_leaf_circle("birch", plant_local_x, top_y, 2, chunk_x, chunk_data)
#     _place_leaf_rectangle("birch", plant_local_x, top_y - 2, 3, 1, chunk_x, chunk_data)


# def _draw_spruce(plant_local_x, bottom_y, chunk_x, chunk_data):
#     # 1. 決定樹幹高度
#     tree_height = random.randint(12, 15)
#     # 2. 畫樹幹 (直接寫入當前的 chunk_data，安全且快速)
#     for y in range(bottom_y, bottom_y - tree_height, -1):
#         if 0 <= y < config.MAP_HEIGHT:
#             chunk_data[y][plant_local_x] = "spruce_log"
#     layers = [
#         1,
#         3,
#         1,
#         3,
#         5,
#         3,
#         5,
#         3,
#         5,
#     ]
#     top_y = bottom_y - tree_height + 1
#     for i, width in enumerate(layers):
#         layer_y = top_y + i
#         _place_leaf_rectangle("spruce", plant_local_x, layer_y, width, 1, chunk_x, chunk_data)


# def _draw_jungle(plant_local_x, bottom_y, chunk_x, chunk_data):
#     # 1. 決定樹幹高度
#     tree_height = random.randint(5, 9)
#     # 2. 畫樹幹 (直接寫入當前的 chunk_data，安全且快速)
#     for y in range(bottom_y, bottom_y - tree_height, -1):
#         if 0 <= y < config.MAP_HEIGHT:
#             chunk_data[y][plant_local_x] = "jungle_log"
#     top_y = bottom_y - tree_height + 1
#     # 下半部 5 x 2 樹葉
#     _place_leaf_rectangle("jungle", plant_local_x, top_y - 1, 5, 2, chunk_x, chunk_data)

#     # 上半部 3 x 2 樹葉
#     _place_leaf_rectangle("jungle", plant_local_x, top_y - 3, 3, 2, chunk_x, chunk_data)


def _draw_chunk(chunk_x, chunk_data):
    for local_x in range(config.CHUNK_WIDTH):
        for y in range(config.MAP_HEIGHT):
            block_type = chunk_data[y][local_x]
            if block_type != "air":
                if local_x < 0 or local_x >= config.CHUNK_WIDTH:
                    continue

                chunk_data[y][local_x] = "oak_log"


# TREE_DRAWERS = {
#     "oak": _draw_oak,
#     "birch": _draw_birch,
#     "spruce": _draw_spruce,
#     "jungle": _draw_jungle,
# }


def _generate_trees(chunk_x, biome_name, chunk_data, height_map, rng: random.Random):

    for local_x in range(config.CHUNK_WIDTH):

        biome = BIOMES[biome_name]

        if biome["tree"] is None:
            continue

        surface_height = height_map[local_x]
        tree_bottom_y = surface_height - 1

        if chunk_data[surface_height][local_x] == "grass":
            if rng.random() < biome["tree_rate"]:
                # 這裡不需要回傳，因為我們直接原地修改傳進去的陣列
                _make_tree(biome["tree"], local_x, tree_bottom_y, chunk_x, chunk_data, rng)

    return chunk_data


def _make_tree(tree_type, plant_local_x, bottom_y, chunk_x, chunk_data, rng: random.Random):
    if tree_type not in TREE_PATTERNS.keys():
        print(f"Unknown tree type: {tree_type}")
        return

    # 呼叫對應的樹生成函數
    # TREE_DRAWERS[tree_type](plant_local_x, bottom_y, chunk_x, chunk_data)
    _draw_tree(tree_type, plant_local_x, bottom_y, chunk_x, chunk_data, rng)


def _place_leaf_rectangle(tree_type, center_x, center_y, width, height, chunk_x, chunk_data, fill=True):
    top = center_y - height // 2

    left = -(width // 2)
    right = width // 2

    for ly in range(top, top + height):
        for lx_offset in range(left, right + 1) if width > 1 else [0]:
            leaf_world_x = (chunk_x * config.CHUNK_WIDTH + center_x) + lx_offset
            _set_leaves_safe(tree_type, leaf_world_x, ly, chunk_x, chunk_data)


def _place_leaf_circle(tree_type, center_x, center_y, radius, chunk_x, chunk_data):
    for ly in range(center_y - radius, center_y + radius + 1):
        dy = ly - center_y
        for dx in range(-radius, radius + 1):
            if dx**2 + dy**2 <= radius**2:
                leaf_world_x = (chunk_x * config.CHUNK_WIDTH + center_x) + dx
                _set_leaves_safe(tree_type, leaf_world_x, ly, chunk_x, chunk_data)


def _place_leaf_diamond(tree_type, center_x, center_y, radius, chunk_x, chunk_data):
    for ly in range(center_y - radius, center_y + radius + 1):
        for lx_offset in range(-radius, radius + 1):
            leaf_world_x = (chunk_x * config.CHUNK_WIDTH + center_x) + lx_offset
            if abs(lx_offset) + abs(ly - center_y) <= radius:
                _set_leaves_safe(tree_type, leaf_world_x, ly, chunk_x, chunk_data)


def _place_leaf_triangle(tree_type, center_x, center_y, height, chunk_x, chunk_data):
    # width = level * 2 + 1
    for ly in range(center_y - height + 1, center_y + 1):
        row_height = center_y - ly
        for lx_offset in range(-row_height, row_height + 1):
            leaf_world_x = (chunk_x * config.CHUNK_WIDTH + center_x) + lx_offset
            _set_leaves_safe(tree_type, leaf_world_x, ly, chunk_x, chunk_data)


def _place_leaf_cross(tree_type, center_x, center_y, radius, chunk_x, chunk_data):
    for ly in range(center_y - radius, center_y + radius + 1):
        dy = ly - center_y
        for dx in range(-radius, radius + 1):
            if abs(dx) == 0 or abs(dy) == 0:
                leaf_world_x = (chunk_x * config.CHUNK_WIDTH + center_x) + dx
                _set_leaves_safe(tree_type, leaf_world_x, ly, chunk_x, chunk_data)


def _place_leaf_ellipse(tree_type, center_x, center_y, width, height, chunk_x, chunk_data):
    a = width / 2
    b = height / 2

    for ly in range(center_y - int(b), center_y + int(b) + 1):
        dy = ly - center_y
        for dx in range(-int(a), int(a) + 1):
            leaf_world_x = (chunk_x * config.CHUNK_WIDTH + center_x) + dx
            if ((dx**2) / (a**2)) + ((dy**2) / (b**2)) <= 1:
                _set_leaves_safe(tree_type, leaf_world_x, ly, chunk_x, chunk_data)


def _set_leaves_safe(tree_type, leaf_world_x, y, current_chunk_x, current_chunk_data):
    """最關鍵的安全樹葉寫入器"""
    if not (0 <= y < config.MAP_HEIGHT):
        return

    # 算出這個葉子落在哪個 chunk 索引，以及它的本地 X
    target_chunk_x = leaf_world_x // config.CHUNK_WIDTH
    local_x = leaf_world_x % config.CHUNK_WIDTH

    # 情況 A：如果樹葉落在當前正在生成的這個 Chunk
    if target_chunk_x == current_chunk_x:
        if current_chunk_data[y][local_x] == "air" or current_chunk_data[y][local_x] == f"{tree_type}_log":
            current_chunk_data[y][local_x] = f"{tree_type}_leaves"

    # 情況 B：如果樹葉飄到旁邊的 Chunk 了
    else:
        # 關鍵：只有當隔壁 Chunk 已經在記憶體中時，我們才寫入
        # 絕對不呼叫 get_chunk() 避免無限遞迴！
        if target_chunk_x in config.chunks:
            neighbor_chunk = config.chunks[target_chunk_x]
            if neighbor_chunk.blocks[y][local_x] == "air" or neighbor_chunk.blocks[y][local_x] == f"{tree_type}_log":
                neighbor_chunk.blocks[y][local_x] = f"{tree_type}_leaves"
                neighbor_chunk.is_dirty = True
