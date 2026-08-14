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
    if not (isinstance(drops, dict) and "material_group" in drops):
        BLOCK_DROPS[pattern] = drops
for pattern, drops in RAW_BLOCK_DROPS.items():
    if isinstance(drops, dict) and "material_group" in drops:
        # 呼叫 expand 展開成一個多個方塊的字典 (例如 {"oak_leaves": {...}, "birch_leaves": {...}})
        expanded_drops = expand_material_drops(pattern, drops)

        for key, drop_data in expanded_drops.items():
            # 🎯 關鍵：如果第一階段已經有特例（如 jungle_leaves），就不被通用模板蓋掉
            if key not in BLOCK_DROPS:
                BLOCK_DROPS[key] = drop_data
