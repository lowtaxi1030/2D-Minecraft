from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from craft_manager import CraftingManager

    # from player import Player
    # from world_manager import World

import config
import craft_manager

TYPES_OF_MATERIAL = ["{wood}_planks", "stone", "iron_ingot", "copper_ingot", "gold_ingot", "diamond"]

RECIPES = [
    {
        "shape": [["{wood}_log"]],
        "ingredients": {"{wood}_log": 1},
        "result_type": "{wood}_planks",
        "result_count": 4,
    },
    {
        "ingredients": {"{wood}_planks": 4},
        "shape": [
            ["{wood}_planks", "{wood}_planks"],
            ["{wood}_planks", "{wood}_planks"],
        ],
        "result_type": "crafting_table",
        "result_count": 1,
    },
    {
        "ingredients": {"{wood}_planks": 6},
        "shape": [
            ["{wood}_planks", "{wood}_planks"],
            ["{wood}_planks", "{wood}_planks"],
            ["{wood}_planks", "{wood}_planks"],
        ],
        "result_type": "{wood}_door",  # 特殊處理
        "result_count": 3,
    },
    # {
    #     "ingredients": {"{wood}_planks": 6},
    #     "shape": [
    #         ["{wood}_planks", "{wood}_planks", "{wood}_planks"],
    #         ["{wood}_planks", "{wood}_planks", "{wood}_planks"],
    #     ],
    #     "result_type": "{wood}_trapdoor",  # 特殊處理
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
        "ingredients": {"{wood}_planks": 2},
        "shape": [
            ["{wood}_planks"],
            ["{wood}_planks"],
        ],
        "result_type": "stick",
        "result_count": 4,
    },
    {
        "ingredients": {"{material}": 3, "stick": 2},
        "shape": [
            ["{material}", "{material}", "{material}"],
            [None, "stick", None],
            [None, "stick", None],
        ],
        "result_type": "{tool_material}_pickaxe",
        "result_count": 1,
    },
    {
        "ingredients": {"{material}": 3, "stick": 2},
        "shape": [
            ["{material}", "{material}", None],
            ["{material}", "stick", None],
            [None, "stick", None],
        ],
        "result_type": "{tool_material}_axe",
        "result_count": 1,
    },
    {
        "ingredients": {"{material}": 1, "stick": 2},
        "shape": [
            [None, "{material}"],
            [None, "stick"],
            [None, "stick"],
        ],
        "result_type": "{tool_material}_shovel",
        "result_count": 1,
    },
    {
        "ingredients": {"{material}": 2, "stick": 2},
        "shape": [
            ["{material}", "{material}"],
            [None, "stick"],
            [None, "stick"],
        ],
        "result_type": "{tool_material}_hoe",
        "result_count": 1,
    },
    {
        "ingredients": {"{material}": 1, "stick": 2},
        "shape": [
            ["{material}", None, None],
            [None, "stick", None],
            [None, None, "stick"],
        ],
        "result_type": "{tool_material}_spear",
        "result_count": 1,
    },
    {
        "ingredients": {"{metal}": 8},
        "shape": [
            ["{metal}", None, "{metal}"],
            ["{metal}", "{metal}", "{metal}"],
            ["{metal}", "{metal}", "{metal}"],
        ],
        "result_type": "{tool_metal}_chestplate",
        "result_count": 1,
    },
    {
        "ingredients": {"{metal}": 7},
        "shape": [
            ["{metal}", "{metal}", "{metal}"],
            ["{metal}", None, "{metal}"],
            ["{metal}", None, "{metal}"],
        ],
        "result_type": "{tool_metal}_leggings",
        "result_count": 1,
    },
    {
        "ingredients": {"{metal}": 5},
        "shape": [
            ["{metal}", "{metal}", "{metal}"],
            ["{metal}", None, "{metal}"],
        ],
        "result_type": "{tool_metal}_helmet",
        "result_count": 1,
    },
    {
        "ingredients": {"{metal}": 4},
        "shape": [
            ["{metal}", None, "{metal}"],
            ["{metal}", None, "{metal}"],
        ],
        "result_type": "{tool_metal}_boots",
        "result_count": 1,
    },
    {
        "ingredients": {"{metal}": 9},
        "shape": [
            ["{metal}", "{metal}", "{metal}"],
            ["{metal}", "{metal}", "{metal}"],
            ["{metal}", "{metal}", "{metal}"],
        ],
        "result_type": "{tool_metal}_block",
        "result_count": 1,
    },
]


def register_recipes(crafting_manager: "CraftingManager"):
    for r in RECIPES:
        # 🎯 檢查配方是否含有 '{wood}' 預留字
        is_wood_template = any("{wood}" in str(k) for k in r["ingredients"].keys()) or "{wood}" in r["result_type"]
        is_material_template = any("{material}" in str(v) for v in r["ingredients"].keys()) or "{tool_material}" in r["result_type"]
        is_metal_template = any("{metal}" in str(v) for v in r["ingredients"].keys()) or "{tool_metal}" in r["result_type"]

        if is_wood_template:
            _handle_wood_recipe(r, crafting_manager)

        elif is_material_template:
            _handle_material_recipe(r, crafting_manager)

        elif is_metal_template:
            _handle_metal_recipe(r, crafting_manager)

        else:
            # 一般普通固定配方
            recipe = craft_manager.ShapeRecipe(
                ingredients=r["ingredients"],
                shape=r["shape"],
                result_type=r["result_type"],
                result_count=r["result_count"],
            )
            crafting_manager.add_recipe(recipe)


def _handle_wood_recipe(r, crafting_manager: CraftingManager):
    # 展開所有木頭 (oak, birch, spruce...)
    for wood in config.TYPES_OF_WOOD:
        # 1. 替換 ingredients (例如: "{wood}_log" -> "oak_log")
        new_ingredients = {item.replace("{wood}", wood): count for item, count in r["ingredients"].items()}

        # 2. 替換 shape
        new_shape = [[item.replace("{wood}", wood) if item is not None else None for item in row] for row in r["shape"]]

        # 3. 替換成品名稱 (例如: "{wood}_planks" -> "oak_planks")
        new_result_type = r["result_type"].replace("{wood}", wood)

        # 建立並註冊配方
        recipe = craft_manager.ShapeRecipe(
            ingredients=new_ingredients,
            shape=new_shape,
            result_type=new_result_type,
            result_count=r["result_count"],
        )
        crafting_manager.add_recipe(recipe)


def _handle_material_recipe(r, crafting_manager: CraftingManager):
    # 🎯 遍歷每一種材質 (例如: ("oak_planks", "wooden"), ("iron_ingot", "iron"))
    for mat_item, tool_prefix in get_all_materials():

        # 1. 替換 ingredients
        new_ingredients = {item.replace("{material}", mat_item): count for item, count in r["ingredients"].items()}

        # 2. 替換 shape 陣列
        new_shape = [[item.replace("{material}", mat_item) if item is not None else None for item in row] for row in r["shape"]]

        # 3. 替換成品名稱 (例如 "{tool_material}_pickaxe" -> "iron_pickaxe")
        new_result_type = r["result_type"].replace("{tool_material}", tool_prefix)

        # 建立並註冊 ShapeRecipe
        recipe = craft_manager.ShapeRecipe(
            ingredients=new_ingredients,
            shape=new_shape,
            result_type=new_result_type,
            result_count=r["result_count"],
        )
        crafting_manager.add_recipe(recipe)


def _handle_metal_recipe(r, crafting_manager: CraftingManager):
    # 🎯 遍歷每一種材質 (例如: ("oak_planks", "wooden"), ("iron_ingot", "iron"))
    for met_item, tool_prefix in get_all_metal():

        # 1. 替換 ingredients
        new_ingredients = {item.replace("{metal}", met_item): count for item, count in r["ingredients"].items()}

        # 2. 替換 shape 陣列
        new_shape = [[item.replace("{metal}", met_item) if item is not None else None for item in row] for row in r["shape"]]

        # 3. 替換成品名稱 (例如 "{tool_metal}_pickaxe" -> "iron_pickaxe")
        new_result_type = r["result_type"].replace("{tool_metal}", tool_prefix)

        # 建立並註冊 ShapeRecipe
        recipe = craft_manager.ShapeRecipe(
            ingredients=new_ingredients,
            shape=new_shape,
            result_type=new_result_type,
            result_count=r["result_count"],
        )
        crafting_manager.add_recipe(recipe)


def get_all_materials() -> list[tuple[str, str]]:
    materials = []
    # 1. 把所有木頭種類展開
    for wood in config.TYPES_OF_WOOD:
        materials.append((f"{wood}_planks", "wooden"))

    # 2. 加入其他一般材質 (材料名, 工具前綴)
    materials.extend(
        [
            ("cobblestone", "stone"),
            ("iron_ingot", "iron"),
            ("copper_ingot", "copper"),
            ("gold_ingot", "golden"),
            ("diamond", "diamond"),
        ]
    )
    return materials


def get_all_metal() -> list[tuple[str, str]]:
    metals = []

    metals.extend(
        [
            ("iron_ingot", "iron"),
            ("copper_ingot", "copper"),
            ("gold_ingot", "golden"),
            ("diamond", "diamond"),
        ]
    )
    return metals
