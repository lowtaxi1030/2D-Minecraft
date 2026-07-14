from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from player import Player

import json
import os

import config


class SaveManager:
    def __init__(self):
        self.world_dir = config.BASE_DIR / "saves" / config.CURRENT_WORLD / "chunks"
        self.info_dir = config.BASE_DIR / "saves" / config.CURRENT_WORLD

    #     self.level_data = {
    #         "seed": config.WORLD_SEED,
    #         "spawn_x": 0,
    #         "spawn_y": 20,
    #         "player": {"x": 0, "y": 20, "hotbar": [None] * 9, "inventory": [None] * 27},
    #     }

    # 儲存
    def save_world(self, player: "Player"):

        self.save_level(player)
        self.save_loaded_chunks()

    def save_level(self, player: "Player"):
        with self.level_path().open("w", encoding="utf-8") as f:
            json.dump(
                {
                    "seed": config.WORLD_SEED,
                    "player": {
                        "x": player.rect.x,
                        "y": player.rect.y,
                        "hotbar": player.hotbar,
                        "inventory": player.inventory,
                    },
                },
                f,
                indent=4,
                ensure_ascii=False,
            )

    def save_loaded_chunks(self):
        for index, chunk in config.chunks.items():
            if not chunk.is_dirty:
                continue

            file_path = self.chunk_path(index)
            with open(file_path, 'w') as f:
                chunk = config.chunks[index]
                json.dump(chunk.blocks, f)
            chunk.is_dirty = False

    # 載入
    def load_world(self, player):
        self.load_level(player)

    def load_level(self, player: "Player"):
        file_path = self.level_path()

        if not file_path.exists():
            return False

        with file_path.open("r", encoding="utf-8") as f:
            level_data = json.load(f)

        config.WORLD_SEED = level_data.get("seed", config.WORLD_SEED)

        player_data = level_data.get("player")

        player.rect.x = player_data.get("x", 0)
        player.rect.y = player_data.get("y", 20 * config.BLOCK_SIZE)
        player.hotbar = player_data.get("hotbar", [None] * 9)
        player.inventory = player_data.get("inventory", [None] * 27)

        return True

    def load_chunk(self, chunk_x):
        file_path = self.chunk_path(chunk_x)
        if not os.path.exists(file_path):
            return None

        with open(file_path) as f:
            loaded_chunk = json.load(f)

        return loaded_chunk

    def chunk_path(self, chunk_x):
        return self.world_dir / f"chunk_{chunk_x}.json"

    def level_path(self):
        return self.info_dir / "level.json"
