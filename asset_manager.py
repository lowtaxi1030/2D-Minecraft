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
