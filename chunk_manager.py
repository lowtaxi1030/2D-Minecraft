from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fluid_manager import FluidManager


import math
import os
import random
import time

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
    "snow": {
        "name": "plains",
        "temp": -0.8,
        "humidity": 0.0,
        "surface": "grass",
        "dirt": "dirt",
        "tree": "oak",
        "tree_rate": 0.03,
        "height": 8,
    },
    "snow_forest": {
        "name": "forest",
        "temp": -0.7,
        "humidity": 0.6,
        "surface": "grass",
        "dirt": "dirt",
        "tree": "oak",
        "tree_rate": 0.15,
        "height": 12,
    },
    "stone_mountain": {
        "name": "birch_forest",
        "temp": -0.3,
        "humidity": -0.5,
        "surface": "grass",
        "dirt": "dirt",
        "tree": "birch",
        "tree_rate": 0.15,
        "height": 12,
    },
    "mountain": {
        "name": "desert",
        "temp": -0.2,
        "humidity": 0.2,
        "surface": "sand",
        "dirt": "sand",
        "tree": None,
        "tree_rate": 0,
        "height": 5,
    },
    "plains": {
        "name": "mountain",
        "temp": 0.0,
        "humidity": -0.2,
        "surface": "grass",
        "dirt": "dirt",
        "tree": "spruce",
        "tree_rate": 0.02,
        "height": 35,
    },
    "forest": {
        "name": "stone_mountain",
        "temp": 0.1,
        "humidity": 0.4,
        "surface": "stone",
        "dirt": "stone",
        "tree": None,
        "tree_rate": 0.02,
        "height": 35,
    },
    "birch_forest": {
        "name": "snow",
        "temp": 0.2,
        "humidity": 0.3,
        "surface": "grass",
        "surface_cover": "snow",
        "dirt": "dirt",
        "tree": "spruce",
        "tree_rate": 0.05,
        "height": 10,
    },
    "dark_forest": {
        "name": "snow_forest",
        "temp": 0.3,
        "humidity": 0.8,
        "surface": "grass",
        "surface_cover": "snow",
        "dirt": "dirt",
        "tree": "spruce",
        "tree_rate": 0.15,
        "height": 10,
    },
    "desert": {
        "name": "jungle",
        "temp": 0.8,
        "humidity": -0.8,
        "surface": "grass",
        "dirt": "dirt",
        "tree": "jungle",
        "tree_rate": 0.25,
        "height": 15,
    },
    "jungle": {
        "name": "dark_forest",
        "temp": 0.7,
        "humidity": 0.9,
        "surface": "grass",
        "dirt": "dirt",
        "tree": "dark_oak",
        "tree_rate": 0.4,  # 樹木密度極高
        "height": 10,
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
    local_y = tool.clamp(0, config.MAP_HEIGHT - 1, y_pos // config.BLOCK_SIZE)

    chunk = get_chunk(chunk_index)

    return chunk.blocks[local_y][local_x]


def set_block(world_x, world_y, block_type):
    # 1. 根據世界格子 X 座標，算出在哪一個 Chunk 區塊
    chunk_i = world_x // config.CHUNK_WIDTH

    # 3. 換算出在該區塊內（0 ~ 15）的相對 X 座標
    local_x = world_x % config.CHUNK_WIDTH
    chunk_y = world_y  # Y 軸是固定的垂直高度，不需要取餘數

    # 4. 寫入方塊（記得照你 make_map 的順序先 Y 後 X）
    chunk = get_chunk(chunk_i)

    chunk.blocks[chunk_y][local_x] = block_type
    chunk.is_dirty = True


def get_chunk(chunk_x, fluid_manager: FluidManager = None) -> Chunk:
    # 1. 已經載入
    if chunk_x in config.chunks:
        return config.chunks[chunk_x]

    # 2. 嘗試讀取存檔
    loaded_chunk = save.load_chunk(chunk_x)
    chunk_world_x = chunk_x * config.CHUNK_WIDTH

    if loaded_chunk is not None:
        biome_name = get_biome(chunk_world_x)

        config.chunks[chunk_x] = Chunk(chunk_x, loaded_chunk, biome_name)
        if fluid_manager is not None:
            fluid_manager.register_chunk_fluids(chunk_x, config.chunks[chunk_x])
        return config.chunks[chunk_x]

    # 3. 沒有存檔就生成
    blocks, biome_name = make_map(config.CHUNK_WIDTH, config.MAP_HEIGHT, chunk_x)

    chunk = Chunk(chunk_x, blocks, biome_name)

    config.chunks[chunk_x] = chunk
    if fluid_manager is not None:
        fluid_manager.register_chunk_fluids(chunk_x, chunk)
    return chunk


def make_map(map_width, map_height, current_chunk_i):
    total_start = time.perf_counter()

    rng = random.Random(
        config.WORLD_SEED + current_chunk_i * 1000003
    )

    biome_name = get_biome(current_chunk_i)

    start = time.perf_counter()
    height_map = _make_terrain(current_chunk_i)
    terrain_time = time.perf_counter() - start

    start = time.perf_counter()
    chunk_data = _make_base_terrain(
        map_width,
        map_height,
        current_chunk_i,
        biome_name,
        height_map,
        rng,
    )
    base_time = time.perf_counter() - start

    start = time.perf_counter()
    chunk_data = _generate_caves(
        current_chunk_i,
        chunk_data,
        height_map,
    )
    caves_time = time.perf_counter() - start

    start = time.perf_counter()
    chunk_data = _generate_cave_entrances(
        current_chunk_i,
        chunk_data,
        height_map,
        rng,
    )
    entrances_time = time.perf_counter() - start

    start = time.perf_counter()
    chunk_data = _generate_trees(
        current_chunk_i,
        biome_name,
        chunk_data,
        height_map,
        rng,
    )
    trees_time = time.perf_counter() - start

    start = time.perf_counter()
    chunk_data = _cleanup_terrain(
        current_chunk_i,
        chunk_data,
        height_map,
    )
    cleanup_time = time.perf_counter() - start

    start = time.perf_counter()
    chunk_data = _generate_underground_fluids(
        current_chunk_i,
        chunk_data,
        height_map,
    )
    fluids_time = time.perf_counter() - start

    start = time.perf_counter()
    chunk_data = _generate_veins(
        current_chunk_i,
        chunk_data,
        rng,
    )
    veins_time = time.perf_counter() - start

    total_time = time.perf_counter() - total_start

    print(
        f"[Chunk {current_chunk_i:>3}] "
        f"總耗時: {total_time:.4f}s | "
        f"Terrain: {terrain_time:.4f}s | "
        f"Base: {base_time:.4f}s | "
        f"Caves: {caves_time:.4f}s | "
        f"Entrances: {entrances_time:.4f}s | "
        f"Trees: {trees_time:.4f}s | "
        f"Cleanup: {cleanup_time:.4f}s | "
        f"Fluids: {fluids_time:.4f}s | "
        f"Veins: {veins_time:.4f}s"
    )

    return chunk_data, biome_name


# 🎯 輔助函式：將原始 Noise 拉平為均勻分布 (-1.0 ~ 1.0)
def _get_uniform_noise(world_x: float, seed: int) -> float:
    noise_x = world_x / config.BIOME_NOISE_SCALE
    raw_noise = opensimplex.noise2(noise_x, seed)
    return math.erf(raw_noise * 1.5)


# 🎯 方案 B 主函式：透過溫度與濕度的 2D 歐幾里得距離決定群系
def get_biome(world_x: int) -> str:
    # 1. 取得校正後的溫度與濕度 (1000, 2000 為不同的種子碼)
    temp_noise = _get_uniform_noise(world_x, 1000)
    humidity_noise = _get_uniform_noise(world_x, 2000)

    best_biome = "plains"
    min_distance = float("inf")

    # 2. 尋找與當前氣候最接近的生態系
    for name, data in BIOMES.items():
        dt = temp_noise - data["temp"]
        dh = humidity_noise - data["humidity"]
        distance = math.hypot(dt, dh)  # 計算 sqrt(dt^2 + dh^2)

        if distance < min_distance:
            min_distance = distance
            best_biome = name

    return best_biome


def _make_terrain(chunk_x):
    config.height_map = []

    # 💡 提示：設定一個隨機種子，讓每次地形都不一樣
    opensimplex.seed(config.WORLD_SEED)

    for local_x in range(config.CHUNK_WIDTH):
        world_x = chunk_x * config.CHUNK_WIDTH + local_x

        raw_noise = opensimplex.noise2(world_x / 30.0, 0)

        # 2. ✨ 關鍵：取 3 次方！這會讓接近 0 的地方大面積變平平的
        # math.copysign 是為了保留原本的正負號（讓它有山也有谷）
        flattened_noise = math.copysign(abs(raw_noise) ** 2.5, raw_noise)

        # 3. 乘以山的高度落差
        noise_val = flattened_noise * 22.0

        current_height = config.BASE_LINE + int(noise_val)

        # 安全防護，防止方塊超出地圖
        current_height = tool.clamp(5, config.MAP_HEIGHT - 5, current_height)
        config.height_map.append(current_height)

    return config.height_map


def _make_base_terrain(map_width, map_height, chunk_x, biome_name, height_map, rng: random.Random):
    chunk_data = [["air"] * map_width for _ in range(map_height)]
    biome = BIOMES[biome_name]
    dirt_depth_map = [rng.randint(3, 5) for _ in range(map_width)]

    # 預先計算每一行 (x) 的 stone_limit，避免在 y 迴圈中重複算 opensimplex
    stone_limits = []
    for x in range(map_width):
        world_x = chunk_x * config.CHUNK_WIDTH + x
        offset = opensimplex.noise2(world_x / 80.0, 500) * 5
        stone_limits.append(int(config.MAP_HEIGHT - 80 + offset))

    for x in range(map_width):
        target_y = height_map[x]
        dirt_end_y = target_y + dirt_depth_map[x]
        stone_limit = stone_limits[x]

        # 表面與土層
        chunk_data[target_y][x] = biome["surface"]
        for y in range(target_y + 1, min(dirt_end_y, config.MAP_HEIGHT)):
            chunk_data[y][x] = biome["dirt"]

        # 石頭層
        for y in range(dirt_end_y, min(stone_limit, config.MAP_HEIGHT)):
            chunk_data[y][x] = "stone"

        # 深板岩層
        for y in range(max(dirt_end_y, stone_limit), config.MAP_HEIGHT - 1):
            chunk_data[y][x] = "deepslate"

        # 基岩
        chunk_data[config.MAP_HEIGHT - 1][x] = "bedrock"

    return chunk_data


def _generate_caves(chunk_x, chunk_data, height_map):
    step = 2  # Y 軸採樣步階，數字越大越快
    base_world_x = chunk_x * config.CHUNK_WIDTH

    for local_x in range(config.CHUNK_WIDTH):
        world_x = base_world_x + local_x
        surface_height = height_map[local_x]
        start_y = surface_height + 5

        # 步階採樣：每 step 格才算一次 Noise
        for y in range(start_y, config.MAP_HEIGHT - 1, step):
            if chunk_data[y][local_x] == "bedrock":
                continue

            cave_noise = opensimplex.noise2(world_x / 20.0, y / 20.0)

            if cave_noise > 0.35:
                # 填補 step 範圍內的格子
                for sy in range(y, min(y + step, config.MAP_HEIGHT - 1)):
                    if chunk_data[sy][local_x] != "bedrock":
                        chunk_data[sy][local_x] = "air"

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
    # 只複製一份出來做讀取，避免邊讀邊改影響結果
    new_chunk = [row[:] for row in chunk_data]

    # 計算這個 Chunk 最高的 surface height，高於此高度太多（如 +10）的全是空氣，不用檢查
    min_surface = min(height_map)
    start_y = max(0, min_surface - 5)

    # 鄰居相對座標偏移量 (8 個方向)
    neighbors_offsets = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
    CAN_CLEAN_BLOCKS = ["stone", "dirt", "deepslate"]

    for y in range(start_y, config.MAP_HEIGHT - 1):
        for local_x in range(config.CHUNK_WIDTH):
            current_block = chunk_data[y][local_x]
            if current_block == "bedrock":
                continue

            air_count = 0
            solid_count = 0
            last_solid_type = ""

            for dx, dy in neighbors_offsets:
                nx, ny = local_x + dx, y + dy
                if 0 <= nx < config.CHUNK_WIDTH and 0 <= ny < config.MAP_HEIGHT:
                    nb = chunk_data[ny][nx]
                    if nb == "air":
                        air_count += 1
                    else:
                        solid_count += 1
                        last_solid_type = nb

            # 第一種：清理孤立單獨的實體方塊
            if current_block in CAN_CLEAN_BLOCKS and air_count >= 7:
                new_chunk[y][local_x] = "air"
            # 第二種：填補孤立單獨的小空洞
            elif current_block in CAN_CLEAN_BLOCKS and solid_count >= 8:
                new_chunk[y][local_x] = last_solid_type

    return new_chunk


def _generate_underground_fluids(chunk_x, chunk_data, height_map):
    for local_x in range(config.CHUNK_WIDTH):
        world_x = chunk_x * config.CHUNK_WIDTH + local_x
        surface_y = height_map[local_x]

        # --- 深度設定 ---
        # 1. 地下水範圍 (淺/中層)
        min_water_y = surface_y + 15
        max_water_y = 90

        # 2. 岩漿範圍 (深層 ~ 基岩上方)
        min_lava_y = max(surface_y + 35, 75)  # 至少要在 Y=75 之後才開始有岩漿
        max_lava_y = config.MAP_HEIGHT - 3  # 留幾格給基岩

        for y in range(config.MAP_HEIGHT):
            if chunk_data[y][local_x] == "bedrock":
                continue

            current_block = chunk_data[y][local_x]

            # --------------------------------------------------
            # 🌋 🔥 岩漿生成邏輯 (優先判定深層)
            # --------------------------------------------------
            if min_lava_y <= y <= max_lava_y:
                # 採用不同的噪聲種子/偏移量 (如 world_x + 500) 避免水脈跟岩漿形狀完全重疊
                lava_noise = opensimplex.noise2((world_x + 500) / 30.0, (y + 500) / 20.0)

                # 越接近地底深處，岩漿生成的門檻越低 (越來越多岩漿)
                lava_depth_factor = (y - min_lava_y) / (max_lava_y - min_lava_y)
                lava_threshold = 0.75 - lava_depth_factor * 0.2  # 最深處門檻降到約 0.55

                if lava_noise > lava_threshold:
                    if current_block in ["air", "stone", "deepslate"]:
                        chunk_data[y][local_x] = "lava_source"
                        continue  # 這裡生成了岩漿，這格就跳過，不繼續塗成水

            # --------------------------------------------------
            # 💧 🌊 地下水生成邏輯 (中/淺層)
            # --------------------------------------------------
            if min_water_y > max_water_y:
                continue
            if min_water_y <= y <= max_water_y:
                water_vein_noise = opensimplex.noise2(world_x / 40.0, y / 25.0)

                water_depth_factor = (y - min_water_y) / max(max_water_y - min_water_y, 1)
                water_threshold = 0.7 - water_depth_factor * 0.15

                if water_vein_noise > water_threshold:
                    if current_block in ["air", "dirt", "stone"]:
                        chunk_data[y][local_x] = "water_source"

    return chunk_data


def _generate_veins(chunk_x, chunk_data, rng: random.Random):
    ore_rules = [
        # =========================
        # Stone
        # =========================
        {
            "name": "coal_ore",
            "seed_offset": 1000,
            "min_y": 60,
            "max_y": 220,
            "scale": 8.0,
            "threshold": 0.6,
            "spawn_chance": 0.05,
            "vein_size": (5, 25),
            "target": "stone",
        },
        {
            "name": "copper_ore",
            "seed_offset": 2000,
            "min_y": 60,
            "max_y": 220,
            "scale": 8.0,
            "threshold": 0.75,
            "spawn_chance": 0.04,
            "vein_size": (4, 8),
            "target": "stone",
        },
        {
            "name": "iron_ore",
            "seed_offset": 3000,
            "min_y": 80,
            "max_y": 220,
            "scale": 10.0,
            "threshold": 0.7,
            "spawn_chance": 0.04,
            "vein_size": (5, 25),
            "target": "stone",
        },
        {
            "name": "gold_ore",
            "seed_offset": 4000,
            "min_y": 70,
            "max_y": 220,
            "scale": 10.0,
            "threshold": 0.75,
            "spawn_chance": 0.025,
            "vein_size": (1, 6),
            "target": "stone",
        },
        {
            "name": "redstone_ore",
            "seed_offset": 5000,
            "min_y": 90,
            "max_y": 220,
            "scale": 12.0,
            "threshold": 0.77,
            "spawn_chance": 0.08,
            "vein_size": (1, 6),
            "target": "stone",
        },
        {
            "name": "lapis_ore",
            "seed_offset": 6000,
            "min_y": 80,
            "max_y": 220,
            "scale": 12.0,
            "threshold": 0.77,
            "spawn_chance": 0.08,
            "vein_size": (2, 8),
            "target": "stone",
        },
        {
            "name": "diamond_ore",
            "seed_offset": 7000,
            "min_y": 90,
            "max_y": 220,
            "scale": 30.0,
            "threshold": 0.78,
            "spawn_chance": 0.01,
            "vein_size": (1, 6),
            "target": "stone",
        },
        {
            "name": "emerald_ore",
            "seed_offset": 8000,
            "min_y": 90,
            "max_y": 220,
            "scale": 12.0,
            "threshold": 0.771,
            "spawn_chance": 0.015,
            "vein_size": (1, 1),
            "target": "stone",
        },
        # =========================
        # Deepslate
        # =========================
        {
            "name": "deepslate_coal_ore",
            "seed_offset": 1000,
            "min_y": 223,
            "max_y": 298,
            "scale": 8.0,
            "threshold": 0.6,
            "spawn_chance": 0.05,
            "vein_size": (5, 20),
            "target": "deepslate",
        },
        {
            "name": "deepslate_copper_ore",
            "seed_offset": 2000,
            "min_y": 223,
            "max_y": 298,
            "scale": 8.0,
            "threshold": 0.75,
            "spawn_chance": 0.04,
            "vein_size": (5, 20),
            "target": "deepslate",
        },
        {
            "name": "deepslate_iron_ore",
            "seed_offset": 3000,
            "min_y": 223,
            "max_y": 298,
            "scale": 10.0,
            "threshold": 0.7,
            "spawn_chance": 0.04,
            "vein_size": (5, 25),
            "target": "deepslate",
        },
        {
            "name": "deepslate_gold_ore",
            "seed_offset": 4000,
            "min_y": 223,
            "max_y": 298,
            "scale": 10.0,
            "threshold": 0.75,
            "spawn_chance": 0.025,
            "vein_size": (1, 6),
            "target": "deepslate",
        },
        {
            "name": "deepslate_redstone_ore",
            "seed_offset": 5000,
            "min_y": 223,
            "max_y": 298,
            "scale": 12.0,
            "threshold": 0.77,
            "spawn_chance": 0.08,
            "vein_size": (1, 6),
            "target": "deepslate",
        },
        {
            "name": "deepslate_lapis_ore",
            "seed_offset": 6000,
            "min_y": 223,
            "max_y": 298,
            "scale": 12.0,
            "threshold": 0.77,
            "spawn_chance": 0.08,
            "vein_size": (2, 8),
            "target": "deepslate",
        },
        {
            "name": "deepslate_diamond_ore",
            "seed_offset": 7000,
            "min_y": 223,
            "max_y": 298,
            "scale": 30.0,
            "threshold": 0.78,
            "spawn_chance": 0.01,
            "vein_size": (1, 6),
            "target": "deepslate",
        },
        {
            "name": "deepslate_emerald_ore",
            "seed_offset": 8000,
            "min_y": 223,
            "max_y": 298,
            "scale": 12.0,
            "threshold": 0.771,
            "spawn_chance": 0.015,
            "vein_size": (1, 1),
            "target": "deepslate",
        },
    ]

    for rule in ore_rules:

        for y in range(config.MAP_HEIGHT):
            for local_x in range(config.CHUNK_WIDTH):

                if chunk_data[y][local_x] != rule["target"]:
                    continue

                if rng.random() > rule["spawn_chance"]:
                    continue

                world_x = chunk_x * config.CHUNK_WIDTH + local_x
                noise = opensimplex.noise2((world_x + rule["seed_offset"]) / rule["scale"], (y + rule["seed_offset"]) / rule["scale"])

                if noise <= rule["threshold"]:
                    continue

                vein_size = rng.randint(*rule["vein_size"])

                _spawn_vein(chunk_data, vein_size, y, local_x, rule["name"], rng)

    return chunk_data


def _spawn_vein(chunk_data, vein_size, center_y, center_x, vein_name, rng: random.Random):
    blocks_placed = 0

    infected_blocks = {(center_x, center_y)}

    if chunk_data[center_y][center_x] not in {
        "stone",
        "deepslate",
    }:
        return

    chunk_data[center_y][center_x] = vein_name
    blocks_placed = 1

    attempts = 0
    max_attempts = vein_size * 5

    directions = (
        (0, 1),
        (0, -1),
        (1, 0),
        (-1, 0),
    )

    while blocks_placed < vein_size and attempts < max_attempts:
        attempts += 1

        base_x, base_y = rng.choice(tuple(infected_blocks))

        dx, dy = rng.choice(directions)

        next_x = base_x + dx
        next_y = base_y + dy

        if not (0 <= next_x < config.CHUNK_WIDTH and 0 <= next_y < config.MAP_HEIGHT):
            continue

        if (next_x, next_y) in infected_blocks:
            continue

        if chunk_data[next_y][next_x] not in {
            "stone",
            "deepslate",
        }:
            continue

        chunk_data[next_y][next_x] = vein_name
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
#  ❗ ❗ 這是特殊的情況 ❗ ❗
# 1 代表必定生成樹葉，0 代表空置，0.5 左右代表有機率生成（營造邊緣落葉質感）
DARK_OAK_LEAF_PATTERNS = [
    [
        [0, 1, 1, 1, 1, 1, 1, 0, 0],
        [1, 1, 1, 1, 1, 1, 1, 1, 1],
        [0, 1, 1, 1, 1, 1, 1, 1, 1],
        [0, 1, 1, 1, 1, 1, 1, 1, 1],
        [0, 0, 0, 1, 1, 1, 1, 0, 0],
        [0, 0, 0, 0, 0, 1, 1, 0, 0],
    ],
    [
        [0, 0, 1, 1, 1, 1, 1, 0, 0],
        [1, 1, 1, 1, 1, 1, 1, 1, 0],
        [1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 0, 0, 0],
        [0, 1, 1, 1, 1, 0, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0, 0, 0],
    ],
    [
        [0, 0, 1, 1, 1, 1, 1, 0, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 0, 0],
        [0, 1, 1, 1, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0, 0, 0],
    ],
    [
        [0, 0, 1, 1, 1, 1, 1, 0, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 0, 0],
        [0, 0, 1, 1, 1, 1, 1, 0, 0],
        [0, 0, 0, 0, 1, 1, 0, 0, 0],
    ],
]


TREE_PATTERNS = {
    "oak": {
        "height": (6, 8),
        "trunk_width": 1,
        "leaves": [[3, 3, 5, 5]],
        "fast_leaf_rate": 0.8,
        "is_2d_matrix": False,
    },  # [4, 6, 7, 9, 8, 7, 7, 2]  阿姆斯特朗炮，之後做
    "birch": {"height": (6, 8), "trunk_width": 1, "leaves": [[1, 3, 3, 5, 5]], "fast_leaf_rate": 0.8, "is_2d_matrix": False},
    "spruce": {
        "height": (10, 14),
        "trunk_width": 1,
        "leaves": [[1, 3, 1, 3, 5, 3, 5, 3, 5], [1, 3, 3, 3]],
        "fast_leaf_rate": 0.8,
        "is_2d_matrix": False,
    },
    "jungle": {"height": (10, 16), "trunk_width": 1, "leaves": [[3, 3, 5, 5]], "fast_leaf_rate": 0.8, "is_2d_matrix": False},
    "dark_oak": {
        "height": (9, 12),
        "trunk_width": 2,
        "leaves": DARK_OAK_LEAF_PATTERNS,
        "fast_leaf_rate": 0.85,
        "is_2d_matrix": True,
    },  # 👈 標記這棵樹使用 2D 矩陣繪製
}


def _generate_trees(chunk_x, biome_name, chunk_data, height_map, rng: random.Random):
    tree_spawn_CD = 7
    placed_tree_x = []

    tree_count = rng.randint(1, 3)  # 每個 chunk 最多生成 1~3 棵樹

    biome = BIOMES[biome_name]

    for _ in range(tree_count):
        for _ in range(10):
            plant_local_x = rng.randint(0, config.CHUNK_WIDTH - 1)
            plant_world_x = chunk_x * config.CHUNK_WIDTH + plant_local_x

            if not _can_place_tree(plant_world_x, placed_tree_x, tree_spawn_CD):
                continue

            surface_y = height_map[plant_local_x]

            if chunk_data[surface_y][plant_local_x] != biome["surface"]:
                continue

            bottom_y = surface_y - 1

            placed_tree_x.append(plant_world_x)
            if TREE_PATTERNS.get(biome["tree"], {}).get("is_2d_matrix"):
                _draw_2d_matrix_tree(biome["tree"], plant_local_x, bottom_y, chunk_x, chunk_data, rng)
            else:
                _draw_symmetry_tree(biome["tree"], plant_local_x, bottom_y, chunk_x, chunk_data, rng)
            break

    return chunk_data


def _can_place_tree(plant_world_x, placed_tree_x, tree_spawn_CD):

    # 距離檢查
    for x in placed_tree_x:
        if abs(plant_world_x - x) < tree_spawn_CD:
            return False

    # 空間檢查

    return True


def _draw_symmetry_tree(tree_type, plant_local_x, bottom_y, chunk_x, chunk_data, rng: random.Random):
    if tree_type not in TREE_PATTERNS:
        # print(f"Unknown tree type: {tree_type}")
        return

    pattern = TREE_PATTERNS[tree_type]
    min_height, max_height = pattern["height"]
    tree_height = rng.randint(min_height, max_height)

    fast_leaf_rate = pattern["fast_leaf_rate"]

    # 畫樹幹
    for y in range(bottom_y, bottom_y - tree_height, -1):
        if not (0 <= y < config.MAP_HEIGHT):
            continue
        for w in range(pattern["trunk_width"]):
            _set_trunk_safe(tree_type, (chunk_x * config.CHUNK_WIDTH + plant_local_x) + w, y, chunk_x, chunk_data)

    # 畫樹冠
    top_y = bottom_y - tree_height + 1
    leaves_pattern = rng.choice(pattern["leaves"])

    for i, width in enumerate(leaves_pattern):
        leaf_y = top_y + i
        _place_leaf_rectangle(tree_type, plant_local_x, leaf_y, width, 1, chunk_x, chunk_data, rng, fast_leaf_rate)


def _draw_2d_matrix_tree(tree_type, plant_local_x, bottom_y, chunk_x, chunk_data, rng: random.Random):
    if tree_type not in TREE_PATTERNS:
        # print(f"Unknown tree type: {tree_type}")
        return

    pattern = TREE_PATTERNS[tree_type]
    min_height, max_height = pattern["height"]
    tree_height = rng.randint(min_height, max_height)

    fast_leaf_rate = pattern["fast_leaf_rate"]

    # 畫樹幹
    for y in range(bottom_y, bottom_y - tree_height, -1):
        if not (0 <= y < config.MAP_HEIGHT):
            continue
        for w in range(pattern["trunk_width"]):
            _set_trunk_safe(tree_type, (chunk_x * config.CHUNK_WIDTH + plant_local_x) + w, y, chunk_x, chunk_data)

    # 畫樹冠（使用 2D 矩陣）
    top_y = bottom_y - tree_height + 1
    leaves_matrix = rng.choice(pattern["leaves"])

    for dy, row in enumerate(leaves_matrix):
        leaf_y = top_y + dy
        for dx, cell in enumerate(row):
            leaf_x = plant_local_x + dx - len(row) // 2  # 中心對齊
            if cell == 1 and 0 <= leaf_x < config.CHUNK_WIDTH and 0 <= leaf_y < config.MAP_HEIGHT:
                is_fast_leaf = rng.random() < fast_leaf_rate
                _set_leaves_safe(tree_type, leaf_x + chunk_x * config.CHUNK_WIDTH, leaf_y, chunk_x, chunk_data, is_fast_leaf=is_fast_leaf)


def _place_leaf_rectangle(
    tree_type, center_x, center_y, width, height, chunk_x, chunk_data, rng: random.Random, fill=True, fast_leaf_rate=0.8
):
    top = center_y - height // 2

    left = -(width // 2)
    right = width // 2

    for ly in range(top, top + height):
        for lx_offset in range(left, right + 1) if width > 1 else [0]:
            leaf_world_x = (chunk_x * config.CHUNK_WIDTH + center_x) + lx_offset
            is_fast_leaf = rng.random() < fast_leaf_rate
            _set_leaves_safe(tree_type, leaf_world_x, ly, chunk_x, chunk_data, is_fast_leaf=is_fast_leaf)


def _set_trunk_safe(tree_type, trunk_world_x, y, current_chunk_x, current_chunk_data):
    if not (0 <= y < config.MAP_HEIGHT):
        return

    # 算出這個葉子落在哪個 chunk 索引，以及它的本地 X
    target_chunk_x = trunk_world_x // config.CHUNK_WIDTH
    local_x = trunk_world_x % config.CHUNK_WIDTH

    log_block = f"{tree_type}_log"

    # 情況 A：如果樹葉落在當前正在生成的這個 Chunk
    if target_chunk_x == current_chunk_x:
        block = current_chunk_data[y][local_x]
        if block == "air":
            current_chunk_data[y][local_x] = log_block

    # 情況 B：如果樹葉飄到旁邊的 Chunk 了
    else:
        # 關鍵：只有當隔壁 Chunk 已經在記憶體中時，我們才寫入
        # 絕對不呼叫 get_chunk() 避免無限遞迴！
        if target_chunk_x in config.chunks:
            neighbor_chunk = config.chunks[target_chunk_x]
            block = neighbor_chunk.blocks[y][local_x]
            if block == "air":
                neighbor_chunk.blocks[y][local_x] = log_block
                neighbor_chunk.is_dirty = True


def _set_leaves_safe(tree_type, leaf_world_x, y, current_chunk_x, current_chunk_data, is_fast_leaf=True):
    """最關鍵的安全樹葉寫入器"""
    if not (0 <= y < config.MAP_HEIGHT):
        return

    # 算出這個葉子落在哪個 chunk 索引，以及它的本地 X
    target_chunk_x = leaf_world_x // config.CHUNK_WIDTH
    local_x = leaf_world_x % config.CHUNK_WIDTH

    leaf = f"{tree_type}_leaves_fast" if is_fast_leaf else f"{tree_type}_leaves"

    # 情況 A：如果樹葉落在當前正在生成的這個 Chunk
    if target_chunk_x == current_chunk_x:
        block = current_chunk_data[y][local_x]
        if block in ("air", f"{tree_type}_log"):
            current_chunk_data[y][local_x] = leaf

    # 情況 B：如果樹葉飄到旁邊的 Chunk 了
    else:
        # 關鍵：只有當隔壁 Chunk 已經在記憶體中時，我們才寫入
        # 絕對不呼叫 get_chunk() 避免無限遞迴！
        if target_chunk_x in config.chunks:
            neighbor_chunk = config.chunks[target_chunk_x]
            block = neighbor_chunk.blocks[y][local_x]
            if block in ("air", f"{tree_type}_log"):
                neighbor_chunk.blocks[y][local_x] = leaf
                neighbor_chunk.is_dirty = True
