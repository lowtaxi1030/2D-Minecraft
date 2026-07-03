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
    SCALE_FACTOR = 0.8

    original_bg = pygame.image.load(f"{str(IMAGE_PATH)}/ui/hotbar_background.png")
    original_frame = pygame.image.load(f"{str(IMAGE_PATH)}/ui/selection_frame.png")
    hotbar_bg = pygame.transform.scale_by(original_bg, SCALE_FACTOR)
    select_frame = pygame.transform.scale_by(original_frame, SCALE_FACTOR)

    hotbar_bg_rect = hotbar_bg.get_rect()
    hotbar_bg_rect.centerx = config.current_width // 2
    hotbar_bg_rect.bottom = config.current_height - 10

    select_frame_rect = select_frame.get_rect()
    select_frame_rect.top = hotbar_bg_rect.top - 3
    select_frame_rect.left = hotbar_bg_rect.left - 1

except FileNotFoundError as e:
    sys.exit(f"找不到 hotbar_bg 或 select_frame 的圖\n{e}")


def update_img_pos(img_rect: pygame.Rect, new_pos: tuple = None, screen_center=True, is_bottom=False):
    """
    更新 UI 圖片位置的工具函式
    :param img_rect: 要修改的 pygame.Rect 物件
    :param new_pos: 自訂座標 (x, y)，如果 screen_center=True 且 is_bottom=True，此參數可不傳
    :param screen_center: 是否水平置中
    :param is_bottom: 是否貼在螢幕底部
    """
    # 1. 處理水平置中
    if screen_center:
        img_rect.centerx = config.current_width // 2
    elif new_pos is not None:
        img_rect.x = new_pos[0]

    # 2. 處理垂直位置（貼底或是指定 Y 軸）
    if is_bottom:
        img_rect.bottom = config.current_height - 10  # 留 10 像素邊距
    elif new_pos is not None:
        img_rect.y = new_pos[1]
