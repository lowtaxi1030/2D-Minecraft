from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from craft_manager import CraftingManager

    # from player import Player
    # from world_manager import World

import config
import craft_manager

RECIPES = [
    {
        "ingredients": {"'all'_log": 1},
        "shape": [["'all'_log"]],
        "result_type": "'all'_planks",
        "result_count": 4,
    },
    {
        "ingredients": {"'all'_planks": 4},
        "shape": [
            ["'all'_planks", "'all'_planks"],
            ["'all'_planks", "'all'_planks"],
        ],
        "result_type": "crafting_table",
        "result_count": 1,
    },
    {
        "ingredients": {"'all'_planks": 6},
        "shape": [
            ["'all'_planks", "'all'_planks"],
            ["'all'_planks", "'all'_planks"],
            ["'all'_planks", "'all'_planks"],
        ],
        "result_type": "'plank_type'_door",  # 特殊處理
        "result_count": 3,
    },
    # {
    #     "ingredients": {"'all'_planks": 6},
    #     "shape": [
    #         ["'all'_planks", "'all'_planks", "'all'_planks"],
    #         ["'all'_planks", "'all'_planks", "'all'_planks"],
    #     ],
    #     "result_type": "'plank_type'_trapdoor",  # 特殊處理
    #     "result_count": 1,
    # },
    {
        "ingredients": {"stone": 8},
        "shape": [
            ["stone", "stone", "stone"],
            ["stone", None, "stone"],
            ["stone", "stone", "stone"],
        ],
        "result_type": "furnace",
        "result_count": 1,
    },
    {
        "ingredients": {"'all'_planks": 2},
        "shape": [
            ["'all'_planks"],
            ["'all'_planks"],
        ],
        "result_type": "stick",
        "result_count": 4,
    },
    {
        "ingredients": {"'all'_planks": 3, "stick": 2},
        "shape": [
            ["'all'_planks", "'all'_planks", "'all'_planks"],
            [None, "stick", None],
            [None, "stick", None],
        ],
        "result_type": "wooden_pickaxe",
        "result_count": 1,
    }
]


def register_recipes(crafting_manager: "CraftingManager"):
    # 石鎬 Recipe
    for r in RECIPES:
        has_wood_template = any("'all'" in key or "'plank_type'" in key for key in r["ingredients"].keys())
        if has_wood_template:
            # 展開所有木頭種類
            for wood in config.TYPES_OF_WOOD:
                # 替換材料名稱中的 'all'
                new_ingredients = {
                    item.replace("'all'", wood).replace("'plank_type'", wood): count for item, count in r["ingredients"].items()
                }
                # 替換成品名稱中的 'all'
                new_shape = [
                    [item.replace("'all'", wood).replace("'plank_type'", wood) if item is not None else None for item in row]
                    for row in r["shape"]
                ]
                new_result_type = r["result_type"].replace("'all'", wood).replace("'plank_type'", wood)

                recipe = craft_manager.ShapeRecipe(
                    ingredients=new_ingredients,
                    shape=new_shape,
                    result_type=new_result_type,
                    result_count=r["result_count"],
                )
                crafting_manager.add_recipe(recipe)
        else:
            # 一般普通配方，直接註冊
            recipe = craft_manager.ShapeRecipe(
                ingredients=r["ingredients"],
                shape=r["shape"],
                result_type=r["result_type"],
                result_count=r["result_count"],
            )
            crafting_manager.add_recipe(recipe)
