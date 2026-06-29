import random


def make_map(map_width, map_height):
    world_data = []
    height_map = _make_terrain(map_width)
    dirt_depth_map = [random.randint(3, 5) for _ in range(map_width)]

    # 橫向一列一列由上往下生成
    for y in range(map_height):
        row = []
        for x in range(map_width):
            target_y = height_map[x]
            # 根據 y 的位置（深度）來決定方塊種類
            if y < target_y:
                block = "air"  # 最上面 10 格是天空
            elif y == target_y:
                block = "grass"  # 第 10 格是表面草地
            elif target_y < y < target_y + dirt_depth_map[x]:
                block = "soil"  # 再往下 4 格是泥土
            else:
                block = "rock"  # 最深處是石頭或礦石（這裡先用你有的煤礦測試）

            row.append(block)
        world_data.append(row)

    return world_data


def _make_terrain(map_width):
    height_map = []
    current_height = 20

    for _ in range(map_width):
        current_height += random.choice([-1, 0, 0, 0, 0, 1])
        height_map.append(current_height)

    return height_map

