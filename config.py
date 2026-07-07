WIDTH, HEIGHT = 1000, 600
current_width, current_height = 1000, 600
scroll_x, scroll_y = 0, 0

BLOCK_SIZE = 60
img_blocks = {}
org_img_blocks = {}
MAP_WIDTH = 1200
MAP_HEIGHT = 140

world_data = []
height_map = []

Timer_Speed = 1

GRAVITY = max(0.1, BLOCK_SIZE / 70)
PLAYER_SPEED = BLOCK_SIZE // 10
PLAYER_RUN_SPEED = BLOCK_SIZE // 5
PLAYER_FLYING_SPEED = BLOCK_SIZE // 4

SLOT_SIZE = 70
PADDING = 5


game_state = "OPTIONS"
