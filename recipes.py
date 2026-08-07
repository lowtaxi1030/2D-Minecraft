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
        "result_type": "'all'_planks",
        "result_count": 4,
    },
    {
        "ingredients": {"'all'_planks": 4},
        "result_type": "crafting_table",
        "result_count": 1,
    },
]


def register_recipes(crafting_manager: "CraftingManager"):
    # 石鎬 Recipe
    for r in RECIPES:
        has_wildcard = any("'all'" in k for k in r["ingredients"].keys()) or "'all'" in r["result_type"]
        if has_wildcard:
            # 展開所有木頭種類
            for wood in config.TYPES_OF_WOOD:
                # 替換材料名稱中的 'all'
                new_ingredients = {item.replace("'all'", wood): count for item, count in r["ingredients"].items()}
                # 替換成品名稱中的 'all'
                new_result_type = r["result_type"].replace("'all'", wood)

                recipe = craft_manager.Recipe(
                    ingredients=new_ingredients,
                    result_type=new_result_type,
                    result_count=r["result_count"],
                )
                crafting_manager.add_recipe(recipe)
        else:
            # 一般普通配方，直接註冊
            recipe = craft_manager.Recipe(
                ingredients=r["ingredients"],
                result_type=r["result_type"],
                result_count=r["result_count"],
            )
            crafting_manager.add_recipe(recipe)
