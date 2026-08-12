import random
from pathlib import Path

GAME_VERSION = "V0.8.4.2"


BASE_DIR = Path(__file__).parent

WIDTH, HEIGHT = 1000, 600
current_width, current_height = 1000, 600

ORG_FOV = 70
fov = 70
BLOCK_SIZE = 50
camera_zoom = 1.0

CHUNK_WIDTH = 16
MAP_HEIGHT = 300

BASE_LINE = 80

chunks = {}
height_map = []

CURRENT_WORLD = "spawn_test2"  # 可以隨意換成任何合法名字
WORLD_SEED = random.randint(0, 999999)

Timer_Speed = 1

SLOT_SIZE = 70
PADDING = 5

game_state = "PLAYING"
running = True

show_debug_screen = False

pause_background = None

TYPES_OF_WOOD = ["oak", "birch", "spruce", "jungle", "acacia", "dark_oak"]
