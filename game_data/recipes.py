from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from craft_manager import CraftingManager

    # from player import Player
    # from world_manager import World

# import config
import craft_manager
from game_data import materials as m

# 之後加"shapeless": True
RECIPES = [
    {
        "material_group": "wood_planks",
        "shape": [["$material_log"]],
        "ingredients": {"$material_log": 1},
        "result_type": "$material_planks",
        "result_count": 4,
    },
    {
        "material_group": "wood_planks",
        "ingredients": {"$material_planks": 4},
        "shape": [
            ["$material_planks", "$material_planks"],
            ["$material_planks", "$material_planks"],
        ],
        "result_type": "crafting_table",
        "result_count": 1,
    },
    {
        "material_group": "wood_planks",
        "ingredients": {"$material_planks": 6},
        "shape": [
            ["$material_planks", "$material_planks"],
            ["$material_planks", "$material_planks"],
            ["$material_planks", "$material_planks"],
        ],
        "result_type": "$material_door",  # 特殊處理
        "result_count": 3,
    },
    {
        "material_group": "wood_planks",
        "ingredients": {"$material_planks": 6},
        "shape": [
            ["$material_planks", "$material_planks", "$material_planks"],
            ["$material_planks", "$material_planks", "$material_planks"],
        ],
        "result_type": "$material_trapdoor",  # 特殊處理
        "result_count": 1,
    },
    {
        "ingredients": {"cobblestone": 8},
        "shape": [
            ["cobblestone", "cobblestone", "cobblestone"],
            ["cobblestone", None, "cobblestone"],
            ["cobblestone", "cobblestone", "cobblestone"],
        ],
        "result_type": "furnace",
        "result_count": 1,
    },
    {
        "material_group": "wood_planks",
        "ingredients": {"$material_planks": 2},
        "shape": [
            ["$material_planks"],
            ["$material_planks"],
        ],
        "result_type": "stick",
        "result_count": 4,
    },
    {
        "material_group": "tool_material",
        "ingredients": {"$material": 3, "stick": 2},
        "shape": [
            ["$material", "$material", "$material"],
            [None, "stick", None],
            [None, "stick", None],
        ],
        "result_type": "$material_pickaxe",
        "result_count": 1,
    },
    {
        "material_group": "tool_material",
        "ingredients": {"$material": 3, "stick": 2},
        "shape": [
            ["$material", "$material", None],
            ["$material", "stick", None],
            [None, "stick", None],
        ],
        "result_type": "$material_axe",
        "result_count": 1,
        "mirrored": True,
    },
    {
        "material_group": "tool_material",
        "ingredients": {"$material": 1, "stick": 2},
        "shape": [
            ["$material"],
            ["stick"],
            ["stick"],
        ],
        "result_type": "$material_shovel",
        "result_count": 1,
    },
    {
        "material_group": "tool_material",
        "ingredients": {"$material": 2, "stick": 2},
        "shape": [
            ["$material", "$material"],
            [None, "stick"],
            [None, "stick"],
        ],
        "result_type": "$material_hoe",
        "result_count": 1,
        "mirrored": True,
    },
    {
        "material_group": "tool_material",
        "ingredients": {"$material": 1, "stick": 2},
        "shape": [
            ["$material", None, None],
            [None, "stick", None],
            [None, None, "stick"],
        ],
        "result_type": "$material_spear",
        "result_count": 1,
        "mirrored": True,
    },
    {
        "material_group": "tool_material",
        "ingredients": {"$material": 2, "stick": 1},
        "shape": [
            ["$material"],
            ["$material"],
            ["stick"],
        ],
        "result_type": "$material_sword",
        "result_count": 1,
    },
    {
        "material_group": "armor",
        "ingredients": {"$material": 8},
        "shape": [
            ["$material", None, "$material"],
            ["$material", "$material", "$material"],
            ["$material", "$material", "$material"],
        ],
        "result_type": "$material_chestplate",
        "result_count": 1,
    },
    {
        "material_group": "armor",
        "ingredients": {"$material": 7},
        "shape": [
            ["$material", "$material", "$material"],
            ["$material", None, "$material"],
            ["$material", None, "$material"],
        ],
        "result_type": "$material_leggings",
        "result_count": 1,
    },
    {
        "material_group": "armor",
        "ingredients": {"$material": 5},
        "shape": [
            ["$material", "$material", "$material"],
            ["$material", None, "$material"],
        ],
        "result_type": "$material_helmet",
        "result_count": 1,
    },
    {
        "material_group": "armor",
        "ingredients": {"$material": 4},
        "shape": [
            ["$material", None, "$material"],
            ["$material", None, "$material"],
        ],
        "result_type": "$material_boots",
        "result_count": 1,
    },
    {
        "material_group": "brick_material",
        "ingredients": {"$material": 9},
        "shape": [
            ["$material", "$material", "$material"],
            ["$material", "$material", "$material"],
            ["$material", "$material", "$material"],
        ],
        "result_type": "$material_block",
        "result_count": 1,
    },
    {
        "material_group": "nugget_material",
        "ingredients": {"$material": 1},
        "shape": [
            ["$material"],
        ],
        "result_type": "$material_nugget",
        "result_count": 9,
    },
    {
        "ingredients": {"iron_ingot": 2},
        "shape": [
            ["iron_ingot", None],
            [None, "iron_ingot"],
        ],
        "result_type": "shears",
        "result_count": 1,
        "mirrored": True,
    },
]


def register_recipes(crafting_manager: CraftingManager):
    for recipe_data in RECIPES:
        # 1. 統一展開：有 material_group 就展開成多筆，沒有就包成單筆串列
        if "material_group" in recipe_data:
            target_recipes = expand_material_recipe(recipe_data)
        else:
            target_recipes = [recipe_data]

        # 2. 統一註冊所有配方
        for recipe in target_recipes:
            # 🎯 情況 A：無形狀配方 (Shapeless)
            if recipe.get("shapeless"):
                crafting_manager.add_recipe(
                    craft_manager.ShapelessRecipe(
                        ingredients=recipe["ingredients"],
                        result_type=recipe["result_type"],
                        result_count=recipe["result_count"],
                    )
                )

            # 🎯 情況 B：有形狀配方 (Shaped)
            else:
                # 新增原本的配方
                crafting_manager.add_recipe(
                    craft_manager.ShapeRecipe(
                        ingredients=recipe["ingredients"],
                        shape=recipe["shape"],
                        result_type=recipe["result_type"],
                        result_count=recipe["result_count"],
                    )
                )

                # 如果有鏡像標記，自動翻轉 shape 並新增第二個 Recipe
                if recipe.get("mirrored"):
                    mirrored_shape = [row[::-1] for row in recipe["shape"]]

                    crafting_manager.add_recipe(
                        craft_manager.ShapeRecipe(
                            ingredients=recipe["ingredients"],
                            shape=mirrored_shape,
                            result_type=recipe["result_type"],
                            result_count=recipe["result_count"],
                        )
                    )


def expand_material_recipe(recipe):
    group_name = recipe["material_group"]
    materials = m.MATERIAL_GROUPS[group_name]

    expanded_recipes = []

    for material, result_item in materials.items():
        ingredients = {key.replace("$material", material): count for key, count in recipe["ingredients"].items()}

        shape = [[cell.replace("$material", material) if cell is not None else None for cell in row] for row in recipe["shape"]]

        result_type = recipe["result_type"].replace("$material", result_item)

        expanded_recipes.append(
            {
                "ingredients": ingredients,
                "shape": shape,
                "result_type": result_type,
                "result_count": recipe["result_count"],
            }
        )

    return expanded_recipes
