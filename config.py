"""提供所有遊戲全域變數"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

import random
from pathlib import Path

GAME_VERSION = "V0.13.5"

# Types
Item = dict[str, str | int]
Pos = tuple[int, int]


BASE_DIR = Path(__file__).parent

WIDTH, HEIGHT = 1000, 600
current_width, current_height = 1000, 600

ORG_FOV = 70
fov = 70
BLOCK_SIZE = 50
SPRINT_ZOOM_MULTIPLIER = 0.9

CHUNK_WIDTH = 16
MAP_HEIGHT = 300

BASE_LINE = 80

CURRENT_WORLD = "test1"  # 可以隨意換成任何合法名字
WORLD_SEED = random.randint(0, 999999)
BIOME_NOISE_SCALE = 700

Timer_Speed = 1

SLOT_SIZE = 70
PADDING = 5

MAX_STACK = 64

game_state = "PLAYING"
running = True

show_debug_screen = False
fps_check = False

pause_background = None

TYPES_OF_WOOD = ["oak", "birch", "spruce", "jungle", "acacia", "dark_oak"]
PLANTABLE_BLOCKS = ["dirt", "grass", "moss_block"]  # 之後加上灰壤
TYPES_OF_FLUID = ["water", "lava"]

ALL_MENUS = ["PAUSE", "OPTION", "VIDEO_OPTION", "CONTROLS_OPTION", "GAME_OPTION"]
