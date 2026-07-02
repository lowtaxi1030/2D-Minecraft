import sys
from pathlib import Path

import pygame

import config

BASE_DIR = Path(__file__).parent

IMAGE_PATH = BASE_DIR / "images"

BLOCKS_PATH = IMAGE_PATH / "blocks"

pygame.init()


def load_all_blocks():

    img_blocks = {}

    # 自動掃描 images 資料夾內所有 png
    for path in BLOCKS_PATH.rglob("*.png"):
        # 取得不含副檔名的名稱，例如 "grass", "coal ore"
        name = path.stem

        # 載入、優化並縮放圖片
        img = pygame.image.load(str(path)).convert_alpha()
        scaled_img = pygame.transform.scale(img, (config.BLOCK_SIZE, config.BLOCK_SIZE))

        # 存入字典
        img_blocks[name] = scaled_img
    return img_blocks


try:
    SCALE_FACTOR = 2

    original_bg = pygame.image.load(f"{str(IMAGE_PATH)}/ui/hotbar_background.png")
    original_frame = pygame.image.load(f"{str(IMAGE_PATH)}/ui/selection_frame.png")
    hotbar_bg = pygame.transform.scale_by(original_bg, SCALE_FACTOR)
    select_frame = pygame.transform.scale_by(original_frame, SCALE_FACTOR)

    hotbar_bg_rect = hotbar_bg.get_rect()
    hotbar_bg_rect.centerx = config.current_width // 2
    hotbar_bg_rect.bottom = config.current_height - 10

except FileNotFoundError as e:
    sys.exit(f"找不到 hotbar_bg 或 select_frame 的圖\n{e}")


def update_img_pos(img_rect: pygame.Rect, new_pos: tuple[int], screen_center=True):
    if screen_center:
        img_rect.centerx = config.current_width // 2
        img_rect.y = new_pos[1]
    else:
        img_rect.x, img_rect.y = new_pos
