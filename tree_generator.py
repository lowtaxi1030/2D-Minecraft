import random

import config


class TreeGenerator:
    def __init__(self):
        self.DARK_OAK_LEAF_PATTERNS = [
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

        self.BIG_SPRUCE_LEAF_PATTERNS = [
            [
                [0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0],
                [0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0],
                [0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0],
                [0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0],
                [0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0],
                [0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0],
                [0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0],
                [0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0],
                [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
                [0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0],
                [0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0],
                [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
                [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            ],
            [
                [0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0],
                [0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0],
                [0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0],
            ],
        ]

        self.TREE_PATTERNS = {
            "oak": {
                "height": (6, 8),
                "trunk_width": 1,
                "trunk_top_gap": 2,
                "leaves": [[3, 3, 5, 5], [3, 5, 5, 5]],
                "fast_leaf_rate": 0.8,
                "is_2d_matrix": False,
            },
            "birch": {
                "height": (6, 8),
                "trunk_width": 1,
                "trunk_top_gap": 3,
                "leaves": [[1, 3, 3, 5, 5]],
                "fast_leaf_rate": 0.8,
                "is_2d_matrix": False,
            },
            "tall_birch": {
                "height": (12, 15),
                "trunk_width": 1,
                "trunk_top_gap": 3,
                "leaves": [[1, 3, 3, 5, 5]],
                "fast_leaf_rate": 0.8,
                "block_type": "birch",
                "is_2d_matrix": False,
            },
            "spruce": {
                "height": (10, 14),
                "trunk_width": 1,
                "trunk_top_gap": 4,
                "leaves": [[1, 3, 1, 3, 5, 3, 5, 3, 5], [1, 3, 1, 3, 5, 3, 5, 7], [1, 3, 3, 3], [1, 3, 5, 3]],
                "fast_leaf_rate": 1.0,
                "is_2d_matrix": False,
            },
            "big_spruce": {
                "height": (20, 25),
                "trunk_width": 2,
                "trunk_top_gap": 2,
                "leaves": self.BIG_SPRUCE_LEAF_PATTERNS,
                "fast_leaf_rate": 1.0,
                "block_type": "spruce",
                "is_2d_matrix": True,
            },
            "jungle": {
                "height": (10, 16),
                "trunk_width": 1,
                "leaves": [[3, 3, 5, 5]],
                "trunk_top_gap": 2,
                "fast_leaf_rate": 0.8,
                "is_2d_matrix": False,
            },
            "dark_oak": {
                "height": (9, 12),
                "trunk_width": 2,
                "leaves": self.DARK_OAK_LEAF_PATTERNS,
                "trunk_top_gap": 4,
                "fast_leaf_rate": 0.85,
                "is_2d_matrix": True,
            },
        }

    # def generate_sapling(self, tree_type, world_x, ground_y, rng): ...

    def generate(self, tree_type: str, world_x: int, ground_y: int, rng: random.Random) -> list[tuple[int, int, str]]:
        """
        生成指定樹種的方塊清單
        ground_y: 樹木立足的地面 Y 座標，樹幹最底層會在 ground_y - 1
        """
        if tree_type not in self.TREE_PATTERNS:
            print(f"[DEBUG]: from tree_generator: no such tree_type called '{tree_type}'")
            return []

        pattern = self.TREE_PATTERNS[tree_type]
        bottom_y = ground_y - 1

        if pattern.get("is_2d_matrix"):
            return self._draw_2d_matrix_tree(tree_type, world_x, bottom_y, rng)
        else:
            return self._draw_symmetry_tree(tree_type, world_x, bottom_y, rng)

    def _can_place_tree(self, plant_world_x, placed_tree_x, tree_spawn_CD):
        for x in placed_tree_x:
            if abs(plant_world_x - x) < tree_spawn_CD:
                return False
        return True

    def _draw_symmetry_tree(self, tree_type: str, world_x: int, bottom_y: int, rng: random.Random):
        pattern = self.TREE_PATTERNS[tree_type]
        block_type = tree_type
        if pattern.get("block_type"):
            block_type = pattern["block_type"]
        tree_height = rng.randint(*pattern["height"])
        fast_leaf_rate = pattern["fast_leaf_rate"]
        trunk_top_gap = pattern.get("trunk_top_gap", 0)
        result = []

        # 畫樹幹
        trunk_positions = set()
        for y in range(bottom_y, bottom_y - tree_height + trunk_top_gap, -1):
            for w in range(pattern["trunk_width"]):
                if block := self._generate_trunk_blocks(block_type, world_x + w, y):
                    result.append(block)
                    trunk_positions.add((block[0], block[1]))

        # 畫樹冠
        top_y = bottom_y - tree_height + 1
        leaves_pattern = rng.choice(pattern["leaves"])

        for i, width in enumerate(leaves_pattern):
            leaf_y = top_y + i
            result.extend(self._place_leaf_rectangle(block_type, world_x, leaf_y, width, 1, rng, fast_leaf_rate, trunk_positions))

        return result

    def _draw_2d_matrix_tree(self, tree_type: str, world_x: int, bottom_y: int, rng: random.Random):
        pattern = self.TREE_PATTERNS[tree_type]
        block_type = tree_type
        if pattern.get("block_type"):
            block_type = pattern["block_type"]
        tree_height = rng.randint(*pattern["height"])
        fast_leaf_rate = pattern["fast_leaf_rate"]
        trunk_top_gap = pattern.get("trunk_top_gap", 0)
        result = []

        # 畫樹幹
        trunk_positions = set()
        for y in range(bottom_y, bottom_y - tree_height + trunk_top_gap, -1):
            for w in range(pattern["trunk_width"]):
                if block := self._generate_trunk_blocks(block_type, world_x + w, y):
                    result.append(block)
                    trunk_positions.add((block[0], block[1]))

        # 畫樹冠（2D 矩陣）
        top_y = bottom_y - tree_height + 1
        leaves_matrix = rng.choice(pattern["leaves"])

        for dy, row in enumerate(leaves_matrix):
            leaf_y = top_y + dy
            for dx, cell in enumerate(row):
                leaf_x = world_x + dx - len(row) // 2
                if cell == 1:
                    is_fast_leaf = rng.random() < fast_leaf_rate
                    if block := self._generate_leaves_blocks(block_type, leaf_x, leaf_y, is_fast_leaf, trunk_positions):
                        result.append(block)

        return result

    def _place_leaf_rectangle(self, block_type, center_x, center_y, width, height, rng: random.Random, fast_leaf_rate=0.8, occupied=None):
        top = center_y - height // 2
        left = -(width // 2)
        right = width // 2
        result = []

        for ly in range(top, top + height):
            for lx_offset in range(left, right + 1) if width > 1 else [0]:
                leaf_world_x = center_x + lx_offset
                is_fast_leaf = rng.random() < fast_leaf_rate
                if block := self._generate_leaves_blocks(block_type, leaf_world_x, ly, is_fast_leaf, occupied):
                    result.append(block)

        return result

    def _generate_trunk_blocks(self, block_type, trunk_world_x, y):
        if not (0 <= y < config.MAP_HEIGHT):
            return None
        return (trunk_world_x, y, f"{block_type}_log")

    def _generate_leaves_blocks(self, block_type, leaf_world_x, y, is_fast_leaf=True, occupied=None):
        if not (0 <= y < config.MAP_HEIGHT):
            return None
        if occupied is not None and (leaf_world_x, y) in occupied:
            return None
        leaf = f"{block_type}_leaves_fast_natural" if is_fast_leaf else f"{block_type}_leaves_natural"
        return (leaf_world_x, y, leaf)
