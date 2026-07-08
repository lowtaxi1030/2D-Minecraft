import sys
from pathlib import Path

import pygame

import config
import tool

BASE_DIR = Path(__file__).parent

IMAGE_PATH = BASE_DIR / "images"

BLOCKS_PATH = IMAGE_PATH / "2d_blocks"

pygame.init()

img_blocks = {}
org_img_blocks = {}


def load_all_blocks():
    global bg_dirt_img, img_blocks, org_img_blocks

    # 自動掃描 images 資料夾內所有 png
    for path in BLOCKS_PATH.rglob("*.png"):
        # 取得不含副檔名的名稱，例如 "grass", "coal ore"
        name = path.stem

        # 載入、優化並縮放圖片
        # 1.存原圖
        org_img = pygame.image.load(str(path)).convert_alpha()
        org_img_blocks[name] = org_img

        # 2. 存縮放後的圖
        scaled_img = tool.scale_img(org_img, config.BLOCK_SIZE)
        img_blocks[name] = scaled_img

    bg_dirt_img = img_blocks["dirt"].copy()
    bg_dirt_img = tool.scale_img(bg_dirt_img, 40)


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

try:
    inventory_img = pygame.image.load(f"{str(IMAGE_PATH)}/ui/inventory.png")
    inventory_img = pygame.transform.scale_by(inventory_img, 3.5)
    inv_rect = inventory_img.get_rect()
    inv_rect.center = (config.WIDTH // 2, config.HEIGHT // 2)

except FileNotFoundError as e:
    sys.exit(f"找不到 inventory 的圖片\n{e}")

try:
    setting_button_img = pygame.image.load(f"{str(IMAGE_PATH)}/ui/setting_button.jpg")
    setting_btn_rect = setting_button_img.get_rect()
    setting_btn_rect.center = (config.WIDTH // 2, config.HEIGHT // 2)

    FOV_bg_img = pygame.image.load(f"{str(IMAGE_PATH)}/ui/FOV.png")
    FOV_bg_img = pygame.transform.scale_by(FOV_bg_img, 0.45)
    FOV_bg_rect = FOV_bg_img.get_rect()

    FOV_lever_img = pygame.image.load(f"{str(IMAGE_PATH)}/ui/FOV_lever.png")
    FOV_lever_img = pygame.transform.scale_by(FOV_lever_img, 0.5)
    FOV_lever_rect = FOV_lever_img.get_rect()

except FileNotFoundError as e:
    sys.exit(f"找不到 setting_button 或 FOV 或 FOV_lever 的圖片\n{e}")


def update_img_pos(img_rect: pygame.Rect, new_pos: tuple = None, y_center=False, screen_center=True, is_bottom=False):
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
        if new_pos is not None:
            img_rect.y = new_pos[1]
    elif new_pos is not None:
        img_rect.x = new_pos[0]

    # 2. 處理垂直位置（貼底或是指定 Y 軸）
    if is_bottom:
        img_rect.bottom = config.current_height - 10  # 留 10 像素邊距
    elif new_pos is not None:
        img_rect.y = new_pos[1]

    if y_center:
        img_rect.centery = config.current_height // 2
