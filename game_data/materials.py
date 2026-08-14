import config

WOOD_PLANKS_GROUP = {wood: wood for wood in config.TYPES_OF_WOOD}

MATERIAL_GROUPS = {
    "wood_planks": WOOD_PLANKS_GROUP,
    "tool_material": {
        **{f"{wood}_planks": "wooden" for wood in config.TYPES_OF_WOOD},
        "cobblestone": "stone",
        "iron_ingot": "iron",
        "copper_ingot": "copper",
        "gold_ingot": "golden",
        "diamond": "diamond",
    },
    "armor": {
        "leather": "leather",
        "iron_ingot": "iron",
        "copper_ingot": "copper",
        "gold_ingot": "golden",
        "diamond": "diamond",
    },
    "metal": {
        "iron_ingot": "iron",
        "copper_ingot": "copper",
        "gold_ingot": "golden",
    },
    "nugget_material": {
        "iron_ingot": "iron",
        "copper_ingot": "copper",
        "gold_ingot": "gold",
    },
    "brick_material": {
        "iron_ingot": "iron",
        "raw_iron": "raw_iron",
        "copper_ingot": "copper",
        "raw_copper": "raw_copper",
        "gold_ingot": "gold",
        "raw_gold": "raw_gold",
        "diamond": "diamond",
        "redstone": "redstone",
        "lapis_lazuli": "lapis",
        "emerald": "emerald",
    },
}

DROPS_GROUPS = {
    "ores": {
        "coal_ore": "coal",
        "iron_ore": "raw_iron",
        "copper_ore": "raw_copper",
        "gold_ore": "raw_gold",
        "redstone_ore": "redstone",
        "lapis_ore": "lapis_lazuli",
        "diamond_ore": "diamond",
        "emerald_ore": "emerald",
        # 深層礦石（Deepslate Ores）也可以順便放進來！
        "deepslate_coal_ore": "coal",
        "deepslate_iron_ore": "raw_iron",
        "deepslate_diamond_ore": "diamond",
        "deepslate_copper_ore": "raw_copper",
        "deepslate_gold_ore": "raw_gold",
        "deepslate_redstone_ore": "redstone",
        "deepslate_lapis_ore": "lapis_lazuli",
        "deepslate_emerald_ore": "emerald",
    }
}
