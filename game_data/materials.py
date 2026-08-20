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
    "nugget_material_rev": {
        "iron_nugget": "iron",
        "copper_nugget": "copper",
        "gold_nugget": "gold",
    },
    "brick_material": {
        "coal": "coal",
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
    "brick_material_rev": {
        "coal_block": "coal",
        "iron_block": "iron_ingot",
        "raw_iron_block": "raw_iron",
        "copper_block": "copper_ingot",
        "raw_copper_block": "raw_copper",
        "gold_block": "gold_ingot",
        "raw_gold_block": "raw_gold",
        "diamond_block": "diamond",
        "redstone_block": "redstone",
        "lapis_block": "lapis_lazuli",
        "emerald_block": "emerald",
    },
}

DROPS_GROUPS = {
    "ores": {
        "coal_ore": "coal",
        "iron_ore": "raw_iron",
        "gold_ore": "raw_gold",
        "diamond_ore": "diamond",
        "emerald_ore": "emerald",
        # "copper_ore": "raw_copper",
        # "redstone_ore": "redstone",
        # "lapis_ore": "lapis_lazuli",
        "deepslate_coal_ore": "coal",
        "deepslate_iron_ore": "raw_iron",
        "deepslate_gold_ore": "raw_gold",
        "deepslate_diamond_ore": "diamond",
        "deepslate_emerald_ore": "emerald",
        # "deepslate_copper_ore": "raw_copper",
        # "deepslate_redstone_ore": "redstone",
        # "deepslate_lapis_ore": "lapis_lazuli",
    }
}
