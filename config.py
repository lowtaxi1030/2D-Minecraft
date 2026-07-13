import random
from pathlib import Path

BASE_DIR = Path(__file__).parent

WIDTH, HEIGHT = 1000, 600
current_width, current_height = 1000, 600

ORG_FOV = 70
fov = 70
BLOCK_SIZE = 50
camera_zoom = 1.0

MAP_WIDTH = 2500
CHUNK_WIDTH = 16
MAP_HEIGHT = 140

chunks = {}
""" 樣式
chunks = {
    0: chunk0,
    1: chunk1,
    2: chunk2,
}
"""
height_map = []
WORLD_SEED = random.randint(0, 999999)

Timer_Speed = 1

SLOT_SIZE = 70
PADDING = 5

game_state = "PLAYING"
running = True

show_debug_screen = False
