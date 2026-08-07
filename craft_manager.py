# from typing import TYPE_CHECKING

# if TYPE_CHECKING:
#     from player import Player
#     from world_manager import World


class ShapeRecipe:
    def __init__(self, ingredients: dict[str, int], shape: list[list[None | str]], result_type: str, result_count: int):
        self.ingredients = ingredients  # ex. {"stone": 3, "stick": 2}  # 材料
        self.shape = shape  # 合成形狀
        self.result = {"type": result_type, "count": result_count}  # ex. {"type": "stone_pickaxe", "count": 1}  # 成品

    def can_craft(self, crafting_grid):
        grid_ingredients = crafting_grid.get_ingredients()
        for item, quantity in self.ingredients.items():
            if grid_ingredients.get(item, 0) < quantity:
                return False
        if crafting_grid.get_trimmed_shape() != self.shape:
            return False
        return True

    def craft(self, crafting_grid):
        if not self.can_craft(crafting_grid):
            return None

        crafting_grid.consume_recipe_materials()

        return self.result.copy()


class CraftingManager:
    def __init__(self):
        self.recipes: list[ShapeRecipe] = []  # 石鎬 Recipe、火把 Recipe、熔爐 Recipe等

    def add_recipe(self, recipe: ShapeRecipe):
        self.recipes.append(recipe)

    def get_recipe(self, ingredients: dict[str, int], crafting_grid) -> ShapeRecipe | None:
        for recipe in self.recipes:
            # 1. 先比對材料「種類」是否完全一致（避免多放雜物）
            if recipe.ingredients.keys() != ingredients.keys():
                continue

            # 2. 再檢查每一種材料的「數量」是否都足夠 (>=)
            is_enough = recipe.can_craft(crafting_grid)

            # 3. 如果種類對、數量也夠，就代表找到正確配方了！
            if is_enough:
                return recipe

        return None

    def craft(self, ingredients, crafting_grid, is_preview=False):
        recipe = self.get_recipe(ingredients, crafting_grid)
        if not recipe:
            return None

        if crafting_grid.get_trimmed_shape() != recipe.shape:
            return None

        # 如果只是預覽，只回傳成品資料，不做任何扣除與生成
        if is_preview:
            # 1. 找出合成盤上所有非空格子的最小物品數量（即最大可合成次數）
            counts = [item["count"] for row in crafting_grid.grid for item in row if item is not None]
            max_crafts = min(counts) if counts else 1

            # 2. 複製一份成品資料，並把數量乘上 max_crafts（最大不超過 64）
            preview_result = recipe.result.copy()
            preview_result["count"] = min(64, preview_result["count"] * max_crafts)

            return preview_result

        # 如果不是預覽（實際點擊），執行真正的合成邏輯
        return recipe.craft(crafting_grid)


class CraftingGrid:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid: list[list[dict[str, int] | None]] = [[None for _ in range(width)] for _ in range(height)]

    def get(self, index: int) -> dict[str, int] | None:
        row = index // self.width
        col = index % self.width
        return self.grid[row][col]

    def get_ingredients(self) -> dict[str, int]:
        ingredients = {}
        for row in range(self.height):
            for col in range(self.width):
                item = self.grid[row][col]
                if item is not None:
                    item_type = item["type"]
                    count = item["count"]
                    ingredients[item_type] = ingredients.get(item_type, 0) + count
        return ingredients

    def set(self, index: int, item: dict[str, int] | None):
        row = index // self.width
        col = index % self.width
        self.grid[row][col] = item

    def consume_recipe_materials(self):  # , recipe: Recipe
        """依據配方需求扣除合成盤裡的材料"""
        # 簡單版（例如 2x2 合成中，凡是有材料的格子數量各自 -1）
        for row in range(self.height):
            for col in range(self.width):
                item = self.grid[row][col]
                if item is None:
                    continue
                item["count"] -= 1
                if item["count"] <= 0:
                    self.grid[row][col] = None

    def get_trimmed_shape(self) -> list[list[str | None]]:
        """
        將合成盤四周無物品的行列裁切掉，只留下物品占據的最小二維陣列。
        例如：
        [None, "oak_log"]
        [None,   None  ]
        裁切後回傳：
        [["oak_log"]]
        """
        items_pos = []
        for r in range(self.height):
            for c in range(self.width):
                if self.grid[r][c] is not None:
                    items_pos.append((r, c))

        if not items_pos:
            return []

        # 找出物品占據的最小與最大行列 index
        min_r = min(r for r, c in items_pos)
        max_r = max(r for r, c in items_pos)
        min_c = min(c for r, c in items_pos)
        max_c = max(c for r, c in items_pos)

        # 根據邊界擷取形狀（只記錄 type 名稱）
        trimmed_shape = []
        for r in range(min_r, max_r + 1):
            row = []
            for c in range(min_c, max_c + 1):
                item = self.grid[r][c]
                row.append(item["type"] if item is not None else None)
            trimmed_shape.append(row)

        return trimmed_shape
