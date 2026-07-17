import random
import sys
from pathlib import Path

import pygame

import config
import tool
from animation_manager import Animation

BASE_DIR = Path(__file__).parent

IMAGE_PATH = BASE_DIR / "images"

BLOCKS_PATH = IMAGE_PATH / "2d_blocks"

pygame.init()

img_blocks = {}
org_img_blocks = {}

LEAVES_COLORS = {
    "oak_leaves": (96, 163, 62),  # 經典溫帶草綠色
    "spruce_leaves": (46, 115, 77),  # 針葉林深藍綠色
    "birch_leaves": (128, 180, 151),  # 樺木偏粉綠、嫩綠色
    "jungle_leaves": (48, 179, 61),  # 雨林鮮綠色
    "desert_leaves": (174, 164, 114),  # 沙漠枯黃色（如果有的話）
}


class AssetManager:
    def __init__(self):
        self.img_blocks = {}
        self.org_img_blocks = {}

        self.hotbar_bg = None
        self.select_frame = None

        self.animations = {}

    def load(self):
        self._load_blocks()

        self._load_hotbar()
        self._load_inventory()
        self._load_setting()

    def _load_blocks(self):

        # 自動掃描 images 資料夾內所有 png
        for path in BLOCKS_PATH.rglob("*.png"):
            # 取得不含副檔名的名稱，例如 "grass", "coal ore"
            name = path.stem

            # 載入、優化並縮放圖片
            if name in LEAVES_COLORS:
                org_img = self._load_and_tint_leaves(str(path), LEAVES_COLORS[name])

            elif name.endswith("_still"):
                print(name)
                self.animations[name] = self._load_animation(str(path))

                org_img = self.animations[name].image

            else:
                org_img = pygame.image.load(str(path)).convert_alpha()
            self.org_img_blocks[name] = org_img

            # 2. 存縮放後的圖
            scaled_img = tool.scale_img(org_img, config.BLOCK_SIZE)
            self.img_blocks[name] = scaled_img

        self.bg_dirt = self.img_blocks["dirt"].copy()
        self.bg_dirt = tool.scale_img(self.bg_dirt, 40)

    def _load_animation(self, path: str):
        frames = []
        sheet = pygame.image.load(path).convert_alpha()

        frame_size = sheet.get_width()  # 256
        frame_count = sheet.get_height() // frame_size
        for i in range(frame_count):
            frame = sheet.subsurface((0, i * frame_size, frame_size, frame_size))
            frame = tool.scale_img(frame, config.BLOCK_SIZE)

            frames.append(frame)
        name = Path(path).stem
        # print(path, len(frames))
        return Animation(name, frames, speed=4, start_frame=random.randint(0, len(frames) - 1))

    def _load_hotbar(self):
        try:
            SCALE_FACTOR = 0.8

            self.original_bg = pygame.image.load(f"{str(IMAGE_PATH)}/ui/hotbar_background.png")
            self.original_frame = pygame.image.load(f"{str(IMAGE_PATH)}/ui/selection_frame.png")
            self.hotbar_bg = pygame.transform.scale_by(self.original_bg, SCALE_FACTOR)
            self.select_frame = pygame.transform.scale_by(self.original_frame, SCALE_FACTOR)

            self.hotbar_bg_rect = self.hotbar_bg.get_rect()
            self.hotbar_bg_rect.centerx = config.current_width // 2
            self.hotbar_bg_rect.bottom = config.current_height - 10

            self.select_frame_rect = self.select_frame.get_rect()
            self.select_frame_rect.top = self.hotbar_bg_rect.top - 3
            self.select_frame_rect.left = self.hotbar_bg_rect.left - 1

        except FileNotFoundError as e:
            sys.exit(f"找不到 hotbar_bg 或 select_frame 的圖\n{e}")

    def _load_inventory(self):
        try:
            self.inventory_img = pygame.image.load(f"{str(IMAGE_PATH)}/ui/inventory.png")
            self.inventory_img = pygame.transform.scale_by(self.inventory_img, 3.5)
            self.inv_rect = self.inventory_img.get_rect()
            self.inv_rect.center = (config.WIDTH // 2, config.HEIGHT // 2)

        except FileNotFoundError as e:
            sys.exit(f"找不到 inventory 的圖片\n{e}")

    def _load_setting(self):
        try:
            self.setting_button_img = pygame.image.load(f"{str(IMAGE_PATH)}/ui/setting_button.jpg")
            self.setting_btn_rect = self.setting_button_img.get_rect()
            self.setting_btn_rect.center = (config.WIDTH // 2, config.HEIGHT // 2)

            self.FOV_bg_img = pygame.image.load(f"{str(IMAGE_PATH)}/ui/FOV.png")
            self.FOV_bg_img = pygame.transform.scale_by(self.FOV_bg_img, 0.45)
            self.FOV_bg_rect = self.FOV_bg_img.get_rect()

            self.FOV_lever_img = pygame.image.load(f"{str(IMAGE_PATH)}/ui/FOV_lever.png")
            self.FOV_lever_img = pygame.transform.scale_by(self.FOV_lever_img, 0.5)
            self.FOV_lever_rect = self.FOV_lever_img.get_rect()

        except FileNotFoundError as e:
            sys.exit(f"找不到 setting_button 或 FOV 或 FOV_lever 的圖片\n{e}")

    def update(self):
        for animation in self.animations.values():
            animation.update()

    def _load_and_tint_leaves(self, image_path: str, tint_color: tuple[int, int, int]):
        # 1. 載入原始灰階圖片，並確保格式支援透明度
        raw_img = pygame.image.load(image_path).convert_alpha()

        # 2. 複製一張新圖片用來染色
        tinted_img = raw_img.copy()

        # 3. 使用 MULTIPLY 混色模式（這會保留黑色的陰影，並把灰色部分染成綠色）
        # 建立一個全綠色的表面
        color_surf = pygame.Surface(tinted_img.get_size(), pygame.SRCALPHA)
        color_surf.fill(tint_color)

        # 將綠色乘上去
        tinted_img.blit(color_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        return tinted_img

    """小工具"""

    def block(self, name):

        animation = self.animations.get(name)
        if animation:
            return self.animations[name].image

        return self.img_blocks[name]

    @staticmethod
    def update_img_pos(img_rect: pygame.Rect, new_pos: tuple = None, y_center=False, screen_center=True, is_bottom=False):
        """
        更新 UI 圖片位置的工具函式
        img_rect: 要修改的 pygame.Rect 物件
        new_pos: 自訂座標 (x, y)，如果 screen_center=True 且 is_bottom=True，此參數可不傳
        screen_center: 是否水平置中
        is_bottom: 是否貼在螢幕底部
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
