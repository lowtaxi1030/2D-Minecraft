from game_data import materials as m

RAW_BLOCK_DROPS = {
    "jungle_leaves": {
        "jungle_sapling": 5,
        "stick": 4,
        None: 31,
    },
    "jungle_leaves_fast": {
        "jungle_sapling": 5,
        "stick": 4,
        None: 31,
    },
    "$material_leaves": {
        "material_group": "wood_planks",
        "$material_sapling": 10,
        "stick": 4,
        "apple": 1,
        None: 25,
    },
    "$material_leaves_fast": {
        "material_group": "wood_planks",
        "$material_sapling": 10,
        "stick": 4,
        "apple": 1,
        None: 25,
    },
    "grass": "dirt",  # 草地挖掉變成泥土
    "stone": "cobblestone",
    "deepslate": "cobbled_deepslate",
    "$material": {
        "material_group": "ores",
        "$material": 1,
    },
    # 特別處理
    "copper_ore": {
        "drop": "raw_copper",
        "count": (2, 5),
    },
    "redstone_ore": {
        "drop": "redstone",
        "count": (4, 5),
    },
    "lapis_ore": {
        "drop": "lapis_lazuli",
        "count": (4, 9),
    },
    "deepslate_copper_ore": {
        "drop": "raw_copper",
        "count": (2, 5),
    },
    "deepslate_redstone_ore": {
        "drop": "redstone",
        "count": (4, 5),
    },
    "deepslate_lapis_ore": {
        "drop": "lapis_lazuli",
        "count": (4, 9),
    },
}


def expand_material_drops(pattern: str, drops_data: dict) -> dict[str, dict]:
    """
    接收帶有 material_group 的掉落物配置，例如：
    pattern = "$material_leaves"
    drops_data = {
        "material_group": "wood_planks",
        "drops": {"$material_sapling": 10, "stick": 4, "apple": 1, None: 25}
    }
    """
    group_name = drops_data["material_group"]
    ALL_GROUPS = {**m.MATERIAL_GROUPS, **m.DROPS_GROUPS}
    materials = ALL_GROUPS[group_name]

    raw_drops = {k: v for k, v in drops_data.items() if k != "material_group"}

    expanded_drops = {}

    for mat_input, mat_result in materials.items():
        # 1. 替換 Key (例如: "$material_leaves" -> "oak_leaves")
        new_key = pattern.replace("$material", mat_input)

        # 2. 替換 drops 內容裡的 $material (例如: "$material_sapling" -> "oak_sapling")
        # raw_drops = drops_data["drops"]
        if isinstance(raw_drops, dict):
            new_drops = {
                (k.replace("$material", mat_result) if isinstance(k, str) else k): v
                for k, v in raw_drops.items()  # v 是機率數字，絕對不能拿去 replace()
            }
        elif isinstance(raw_drops, str):
            new_drops = raw_drops.replace("$material", mat_input)
        else:
            new_drops = raw_drops

        expanded_drops[new_key] = new_drops

    return expanded_drops


BLOCK_DROPS = {}

for pattern, drops in RAW_BLOCK_DROPS.items():
    # 1. 如果有 material_group，進行群組展開
    if isinstance(drops, dict) and "material_group" in drops:
        expanded_drops = expand_material_drops(pattern, drops)

        for key, drop_data in expanded_drops.items():
            # 優先保留第一階段已定義的特例
            if key not in BLOCK_DROPS:
                BLOCK_DROPS[key] = drop_data

    # 2. 普通設定或包含 count 的特殊設定 (如 copper_ore, redstone_ore)
    else:
        BLOCK_DROPS[pattern] = drops
