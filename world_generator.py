import random


def make_map(map_width, map_height):
    world_data = []
    height_map = _make_terrain(map_width)
    dirt_depth_map = [random.randint(3, 5) for _ in range(map_width)]
    rock_depth_map = [random.randint(25, 40) for _ in range(map_width)]

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
            elif y == target_y:
                block = "grass"  # 第 10 格是表面草地
            elif target_y < y < dirt_end_y:
                block = "soil"  # 再往下 4 格是泥土
            elif y < dirt_end_y + rock_depth_map[x]:
                block = "rock"
            else:
                block = "deepslate"

            row.append(block)
        world_data.append(row)

    world_data = _generate_veins(world_data, map_width, map_height)
    world_data = _generate_veins(world_data, map_width, map_height)

    return world_data


def _make_terrain(map_width):
    height_map = []
    current_height = 20

    for _ in range(map_width):
        current_height += random.choice([-1, 0, 0, 0, 0, 1])
        height_map.append(current_height)

    return height_map


def _generate_veins(world_data, map_width, map_height):
    # 🛠️ 在這裡集中管理所有礦物的生成規則，要新增礦物只要在這邊加一行就好！
    ore_rules = [
        # {"name": 礦物名稱, "min_y": 最高高度, "max_y": 最低高度, "veins_range": 群落數範圍, "size_range": 每坨大小, "target_stones": 能替換的石頭}
        {"name": "iron ore", "min_y": 15, "max_y": 58, "veins_range": (5, 10), "size_range": (5, 18), "target_stones": ["rock"]},
        {"name": "coal ore", "min_y": 15, "max_y": 58, "veins_range": (5, 10), "size_range": (5, 25), "target_stones": ["rock"]},
        {"name": "copper ore", "min_y": 20, "max_y": 58, "veins_range": (5, 10), "size_range": (4, 8), "target_stones": ["rock"]},
        {"name": "gold ore", "min_y": 20, "max_y": 58, "veins_range": (3, 7), "size_range": (4, 8), "target_stones": ["rock"]},
        {"name": "diamond ore", "min_y": 40, "max_y": 58, "veins_range": (1, 3), "size_range": (1, 6), "target_stones": ["rock"]},
        {"name": "deepslate IO", "min_y": 60, "max_y": 119, "veins_range": (8, 15), "size_range": (5, 18), "target_stones": ["deepslate"]},
        {"name": "deepslate CO", "min_y": 60, "max_y": 119, "veins_range": (8, 15), "size_range": (5, 20), "target_stones": ["deepslate"]},
        {"name": "deepslate EO", "min_y": 80, "max_y": 119, "veins_range": (3, 8), "size_range": (1, 1), "target_stones": ["deepslate"]},
        {"name": "deepslate DO", "min_y": 60, "max_y": 119, "veins_range": (2, 5), "size_range": (1, 6), "target_stones": ["deepslate"]},
    ]

    # ✨ 核心魔法：用一個迴圈，把所有礦物的規則依序拿出來跑
    for rule in ore_rules:
        # 根據當前礦物的規則，隨機決定這次要生幾坨礦脈
        num_of_veins = random.randint(rule["veins_range"][0], rule["veins_range"][1])

        for _ in range(num_of_veins):
            while True:
                center_x = random.randint(0, map_width - 1)
                # 使用規則裡指定的 Y 軸範圍
                center_y = random.randint(rule["min_y"], rule["max_y"])

                # 確保起點是該礦物「允許替換」的岩石類型
                if world_data[center_y][center_x] in rule["target_stones"]:
                    break

            # 隨機決定這坨的大小
            vein_size = random.randint(rule["size_range"][0], rule["size_range"][1])

            # 呼叫你原本寫好的漂亮蔓延函式！
            _veins_spawn(world_data, vein_size, center_y, center_x, map_width, map_height, rule["name"])

    return world_data


def _veins_spawn(world_data, vein_size, center_y, center_x, map_width, map_height, vein_name):
    blocks_placed = 0

    # 建立一個「已經被感染」的方塊坐標清單，起點是中心
    # 使用 set 是為了方便快速判斷某格是不是已經變成鐵礦了
    infected_blocks = set()
    infected_blocks.add((center_x, center_y))

    # 先把中心點放下去
    if world_data[center_y][center_x] in ["rock", "deepslate"]:
        world_data[center_y][center_x] = vein_name
        blocks_placed += 1

    # 用 while 確保一定要放滿指定格數
    while blocks_placed < vein_size:
        # ✨ 關鍵修改：從「所有已經感染的方塊」中隨機挑選一個
        # 這樣我們就像從已經生好的礦塊邊緣隨機「突觸」一格，不會一直跑遠
        base_x, base_y = random.choice(list(infected_blocks))

        # 從這個挑選到的「突觸點」隨機抽一個上下左右的方向
        dx, dy = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
        next_x = max(0, min(map_width - 1, base_x + dx))
        next_y = max(0, min(map_height - 1, base_y + dy))

        # 如果下一個位置是石頭，且還沒被感染
        if world_data[next_y][next_x] in ["rock", "deepslate"] and (next_x, next_y) not in infected_blocks:
            # 放下礦石
            world_data[next_y][next_x] = vein_name
            # 把這格加入「被感染清單」，下次也可能從這格突觸
            infected_blocks.add((next_x, next_y))
            blocks_placed += 1
