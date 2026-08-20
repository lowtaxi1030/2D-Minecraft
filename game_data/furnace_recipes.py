import config
from game_data import materials as m

RAW_FURNACE_RECIPES = [
    {
        "input": "raw_iron",
        "result_type": "iron_ingot",
        "result_count": 1,
        "cook_time": 600,
    },
    {
        "input": "raw_gold",
        "result_type": "gold_ingot",
        "result_count": 1,
        "cook_time": 600,
    },
    {
        "input": "raw_copper",
        "result_type": "copper_ingot",
        "result_count": 1,
        "cook_time": 600,
    },
    {
        "input": "cobblestone",
        "result_type": "stone",
        "result_count": 1,
        "cook_time": 600,
    },
    {
        "input": "stone",
        "result_type": "smooth_stone",
        "result_count": 1,
        "cook_time": 600,
    },
    {
        "material_group": "wood_planks",
        "input": "$material_log",
        "result_type": "charcoal",
        "result_count": 1,
        "cook_time": 600,
    },
]

def expand_furnace_recipe(recipe: dict) -> list[dict]:
    group_name = recipe["material_group"]
    materials = m.MATERIAL_GROUPS[group_name]  #[cite: 6]

    expanded_recipes = []

    for item_key, mat_value in materials.items():
        # 提取底層材料名稱 (例如 "oak_planks" -> "oak"[cite: 6])
        clean_mat = item_key.replace("_planks", "").replace("_log", "")

        # 1. 處理輸入物品 (支援 $material 與自訂字串)
        input_item = recipe["input"].replace("$material", clean_mat)

        # 2. 處理輸出物品 (支援 $material 與對應群組 value[cite: 6])
        result_type = recipe["result_type"].replace("$material", mat_value)

        expanded_recipes.append(
            {
                "input": input_item,
                "result_type": result_type,
                "result_count": recipe["result_count"],
                "cook_time": recipe.get("cook_time", 600),
            }
        )

    return expanded_recipes

FURNACE_RECIPES = {}

for recipe in RAW_FURNACE_RECIPES:
    if "material_group" in recipe:
        # 展開群組配方
        for expanded in expand_furnace_recipe(recipe):
            FURNACE_RECIPES[expanded["input"]] = expanded
    else:
        # 一般單一配方 (例如 stone -> smooth_stone)
        FURNACE_RECIPES[recipe["input"]] = recipe

FURNACE_FUELS = {
    "coal": 4800,
    "charcoal": 4800,
    "stick": 30,
    **dict.fromkeys([f"{wood}_planks" for wood in config.TYPES_OF_WOOD], 900),
    **dict.fromkeys([f"{wood}_log" for wood in config.TYPES_OF_WOOD], 900),
}


def get_recipe(item_type: str):
    """根據輸入物品類型，取得對應的熔爐配方；若無配方則回傳 None"""
    return FURNACE_RECIPES.get(item_type)
