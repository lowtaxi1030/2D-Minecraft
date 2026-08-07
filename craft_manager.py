# from typing import TYPE_CHECKING

# if TYPE_CHECKING:
#     from player import Player
#     from world_manager import World


class Recipe:
    def __init__(self, ingredients: dict[str, int], result_type: str, result_count: int):
        self.ingredients = ingredients  # ex. {"stone": 3, "stick": 2}  # 材料
        self.result = {"type": result_type, "count": result_count}  # ex. {"type": "stone_pickaxe", "count": 1}  # 成品

    def can_craft(self, crafting_grid):
        grid_ingredients = crafting_grid.get_ingredients()
        for item, quantity in self.ingredients.items():
            if grid_ingredients.get(item, 0) < quantity:
                return False
        return True

    def craft(self, crafting_grid):
        if not self.can_craft(crafting_grid):
            return None

        crafting_grid.consume_recipe_materials()

        return self.result.copy()


class CraftingManager:
    def __init__(self):
        self.recipes: list[Recipe] = []  # 石鎬 Recipe、火把 Recipe、熔爐 Recipe等

    def add_recipe(self, recipe: Recipe):
        self.recipes.append(recipe)

    def get_recipe(self, ingredients: dict[str, int]) -> Recipe | None:
        for recipe in self.recipes:
            # 1. 先比對材料「種類」是否完全一致（避免多放雜物）
            if recipe.ingredients.keys() != ingredients.keys():
                continue

            # 2. 再檢查每一種材料的「數量」是否都足夠 (>=)
            is_enough = True
            for item_name, required_count in recipe.ingredients.items():
                if ingredients.get(item_name, 0) < required_count:
                    is_enough = False
                    break

            # 3. 如果種類對、數量也夠，就代表找到正確配方了！
            if is_enough:
                return recipe

        return None

    def craft(self, ingredients, crafting_grid, is_preview=False):
        recipe = self.get_recipe(ingredients)
        if not recipe:
            return None if is_preview else False

        # 1. 如果只是預覽，只回傳成品資料，不做任何扣除與生成
        if is_preview:
            return recipe.result

        # 2. 如果不是預覽（實際點擊），執行真正的合成邏輯
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
