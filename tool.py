from __future__ import annotations

import math
import os
import pathlib
import platform as plat
import subprocess as sub
from math import cos, radians, sin

import pygame as p

import asset_manager as assets
import config

# 初始化 p (必須先初始化才能使用字體)
p.init()
p.mixer.init()

# clock = p.time.Clock()
# 設定全域變數
T, F = True, False
s = p.display.set_mode((config.current_width, config.current_height))


# class RangeError(Exception):
#     __module__ = "builtins"


class CR:  # ColoredRect
    def __init__(self, rect, color, show=True, can_collide=True):
        self.rect = rect  # p.Rect
        self.color = color  # (R, G, B)
        self.show = show
        self.can_collide = can_collide

    def draw(self, surface):
        if self.show:
            p.draw.rect(surface, self.color, self.rect)


Color = tuple[int, int, int]


class Colors:
    """提供各種顏色 (依色相與色調排序)"""

    # 1. 基礎與深色系 (最適合當遊戲背景)
    # 這組顏色飽和度較低或亮度較暗，不會干擾玩家看清子彈或敵人。

    BLACK = (0, 0, 0)
    BLACK2 = (30, 30, 30)  # 推薦：World 1 背景
    BLACK_3 = (60, 60, 60)
    DARK_GRAY = (100, 100, 100)
    BLUE3 = (50, 0, 100)  # 推薦：神祕關卡背景
    TYRIAN_PURPLE = (102, 2, 60)  # 推薦：Boss 關背景

    # 2. 暖色調 (紅、橙、黃、金)
    # 這組適合當「警示」、「熔岩世界」或「解鎖按鈕」。

    RED = (255, 0, 0)
    RED_2 = (200, 0, 0)
    DARK_RED = (160, 0, 0)
    LIGHT_RED = (255, 80, 80)
    VERMILION = (255, 50, 0)
    ORANGE = (255, 100, 0)
    ORANGE2 = (200, 50, 0)
    BROWN = (200, 100, 50)  # 推薦：荒漠世界
    GOLD = (255, 215, 0)
    YELLOW = (255, 255, 0)
    MC_YELLOW = (255, 255, 160)

    # 3. 綠色調 (森林、草地、毒液)
    DARK_GREEN = (0, 100, 0)  # 推薦：叢林背景
    OLIVE = (127, 127, 0)
    EMERALD = (80, 180, 130)
    PARIS_GREEN = (80, 200, 120)
    CHARTREUSE = (127, 255, 0)
    GREEN = (0, 255, 0)

    # 4. 冷色調 (青、藍、紫、粉)
    # 這組適合「水下世界」、「科技感」或「稀有皮膚」。
    BLUE2 = (0, 0, 170)
    BLUE = (0, 0, 255)
    CYAN = (135, 206, 235)  # 推薦：冰雪/水下世界背景
    VIOLET = (143, 0, 255)
    PURPLE = (128, 0, 128)
    FUCHSIA = (255, 50, 180)
    PINK = (255, 0, 255)
    CLARET = (191, 0, 64)

    # 5. 高亮度與特殊色
    # 適合文字、UI 邊框或發光特效。
    COSMIC_LATTE = (255, 248, 231)
    WHITE = (255, 255, 255)
    GRAY = (160, 160, 160)

    # 萬聖節顏色
    PUMPKIN_ORANGE = (255, 117, 24)
    MIDNIGHT_PURPLE = (75, 0, 130)  # 這跟你現在的 BLUE3 背景很搭！
    SLIME_GREEN = (50, 205, 50)
    BLOOD_RED = (138, 7, 7)

    # 實驗中顏色
    TEST_COLOR = (127, 255, 0)

    @staticmethod
    def get_color(color_name: str, default=WHITE):
        # 將輸入轉為大寫，並嘗試從類別屬性中抓取
        if color_name.upper() == "DARK ORANGE":
            color_name = "ORANGE 2"
        if color_name.upper() == "LIGHT BLUE":
            color_name = "CYAN"
        return getattr(Colors, color_name.upper().replace(" ", "_"), default)

    @staticmethod
    def two_color_gradient(color1: Color, color2: Color, ratio: float):
        """ratio 是 color1 的比例，回傳兩個顏色的漸層色"""
        ratio = clamp(0, 1, ratio)
        r = int(color1[0] * ratio + color2[0] * (1 - ratio))
        g = int(color1[1] * ratio + color2[1] * (1 - ratio))
        b = int(color1[2] * ratio + color2[2] * (1 - ratio))
        return (r, g, b)

    @staticmethod
    def two_color_wave(color1: Color, color2: Color, speed: int | float, time_func=p.time.get_ticks):
        """根據時間在兩個顏色之間波動，\n time_func 是要用的時間函式，預設是 p 的 get_ticks()"""

        ratio = (sin(time_func() / 1000.0 * speed) + 1) / 2  # 產生 0 到 1 的波動
        return Colors.two_color_gradient(color1, color2, ratio)

    @staticmethod
    def two_color_change(color1: Color, color2: Color, condition: bool):
        """condition 為 True 時回傳 color1, 為 False 時回傳 color2"""
        return color1 if condition else color2


text_cache = {}

root = pathlib.Path(__file__).parent.resolve(strict=False)

defult_font = p.font.Font(str(root / "Minecraft.ttf"), 24)


AlphaColor = tuple[int, int, int, int]


def show_text(screen, text, text_color, x, y, size=24, center=False, screen_center=False, show=True, font_type="", alpha=255, line_gap=5):
    # 1. 產生唯一的快取 Key (包含 alpha 也要放進去，因為 alpha 不同圖片就不同)
    # 如果 text 是清單，轉成字串來當 key
    text_str = "".join(text) if isinstance(text, list) else text
    key = (text_str, text_color, size, font_type, alpha)

    # 2. 檢查快取：如果這組文字已經畫過了，直接拿出來 blit
    if key in text_cache:
        surfaces, relative_rects = text_cache[key]
    else:
        # --- 以下內容只有在「第一次畫這段字」時才會執行 ---
        surfaces = []
        relative_rects = []

        # 字體初始化 (這也很耗時，只有沒快取才做)
        if font_type == "":
            font = p.font.Font(str(root / "Minecraft.ttf"), size)
        elif font_type == "None":
            font = p.font.SysFont(None, size)
        else:
            font = p.font.SysFont(font_type, size)

        text_list = [text] if isinstance(text, str) else text

        temp_y = 0
        for t in text_list:
            # 渲染並處理透明度
            t_surf = font.render(t, True, text_color)
            final_surf = p.Surface(t_surf.get_size(), p.SRCALPHA).convert_alpha()  # 記得加 convert_alpha
            final_surf.blit(t_surf, (0, 0))
            if alpha < 255:
                final_surf.set_alpha(alpha)

            # 儲存 Surface
            surfaces.append(final_surf)

            # 儲存相對位置 (以 y=0 為起點，方便後續根據傳入的 y 移動)
            t_rect = final_surf.get_rect()
            t_rect.top = temp_y
            relative_rects.append(t_rect)

            temp_y = t_rect.bottom + line_gap

        # 存入快取：把這一組 Surface 和它們的相對位置存起來
        text_cache[key] = (surfaces, relative_rects)

    # 3. 繪製邏輯 (這一部分每一幀都會跑，但現在只剩 blit，非常快)
    first_rect = None
    total_text_height = relative_rects[-1].bottom if relative_rects else 0
    for i, surf in enumerate(surfaces):
        # 複製一份矩形來做位置偏移計算
        draw_rect = relative_rects[i].copy()

        # 根據外部傳入的 x, y 進行偏移
        if center:
            line_center_offset_y = relative_rects[i].top + (draw_rect.height / 2) - (total_text_height / 2)
            draw_rect.center = (x, y + line_center_offset_y)
        else:
            draw_rect.top = y + relative_rects[i].top
            if screen_center:
                draw_rect.centerx = screen.get_rect().w // 2
            else:
                draw_rect.x = x

        if i == 0:
            first_rect = draw_rect
        if show:
            screen.blit(surf, draw_rect)

    return first_rect


class Button:
    def __init__(
        self,
        name: str,
        rect: p.Rect,
        normal_color: Color | AlphaColor,
        pressing_color: Color | AlphaColor | None = None,
        hover_color: Color | AlphaColor | None = None,
        disabled_color: Color | AlphaColor | None = None,
        border_radius=5,
        border_width=None,
        normal_border_color: Color | AlphaColor = None,
        pressing_border_color: Color | AlphaColor | None = None,
        hover_border_color: Color | AlphaColor | None = None,
        disabled_border_color: Color | AlphaColor | None = None,
        show=True,
        color_wave: None | list[Color] = None,
        screen_center=False,
    ):
        self.name = name
        self.org_rect = rect
        self.draw_rect = self.org_rect.copy()
        self.base_y = rect.y
        self.border_radius = border_radius
        self.border_width = border_width
        self.active = True
        self.toggle = False
        self.is_hover = False
        self.is_down = False
        self.is_hoding = False
        self.is_clicked = False
        self.type = "normal"

        # 按鈕顏色保底
        self.normal_color = normal_color
        self.hover_color = hover_color if hover_color is not None else normal_color
        self.pressing_color = pressing_color if pressing_color is not None else self.hover_color
        self.disabled_color = disabled_color if disabled_color is not None else Colors.GRAY

        # 按鈕邊框顏色保底
        self.normal_border_color = normal_border_color if normal_border_color is not None else normal_color
        self.hover_border_color = hover_border_color if hover_border_color is not None else self.normal_border_color
        self.pressing_border_color = pressing_border_color if pressing_border_color is not None else self.hover_border_color
        self.disabled_border_color = disabled_border_color if disabled_border_color is not None else Colors.GRAY

        self.is_visible = show
        self.color_wave = color_wave

        self.screen_center = screen_center

    def change_base_color(self, new_color, force=False):
        self.normal_color = new_color
        if force:
            self.hover_color = new_color
            self.pressing_color = new_color
            self.disabled_color = new_color
        else:
            # 修改處
            self.hover_color = self.hover_color if self.hover_color is not None else self.normal_color
            self.pressing_color = self.pressing_color if self.pressing_color is not None else self.hover_color

    def change_base_border_color(self, new_color, force=False):
        self.normal_border_color = new_color
        if force:
            self.hover_border_color = new_color
            self.pressing_border_color = new_color
            self.disabled_border_color = new_color
        else:
            # 修改處
            self.hover_border_color = self.hover_border_color if self.hover_border_color is not None else self.normal_border_color
            self.pressing_border_color = self.pressing_border_color if self.pressing_border_color is not None else self.hover_border_color

    def get_color(self):
        if not self.active:
            return self.disabled_color

        if self.is_hoding:
            return self.pressing_color

        if self.is_hover:
            return self.hover_color

        return self.normal_color

    def get_border_color(self):
        if not self.active:
            return self.disabled_border_color

        if self.is_hoding:
            return self.pressing_border_color

        if self.is_hover:
            return self.hover_border_color

        return self.normal_border_color

    def handle_condition(self, condition: bool, value1, value2):
        return value1 if condition else value2

    def update(self, events, mouse_pos):
        if not self.is_visible or not self.active:
            self.is_down = False
            self.is_clicked = False
            return

        # 每幀重置（重要）
        self.is_clicked = False

        # hover
        self.is_hover = self.draw_rect.collidepoint(mouse_pos)

        for event in events:
            # 按下
            if event.type == p.MOUSEBUTTONDOWN and event.button == 1:
                if self.is_hover:
                    self.is_down = True
                    self.is_hoding = True
            # 放開
            if event.type == p.MOUSEBUTTONUP and event.button == 1:
                self.is_hoding = False
                if self.is_down and self.is_hover:
                    self.is_clicked = True

                self.is_down = False
        if self.type == "hold":
            if self.is_down and self.is_hover:
                self.is_clicked = True
        elif self.type == "toggle":
            if self.is_clicked:
                self.toggle = not self.toggle

    def draw(self, screen: p.Surface, alpha=255):
        if not self.is_visible:
            return

        # 計算繪製位置
        self.draw_rect = self.org_rect.copy()

        if self.screen_center:
            self.draw_rect.centerx = screen.get_rect().centerx

        # 建立支援透明度的臨時畫布
        surface = p.Surface(self.draw_rect.size, p.SRCALPHA)
        color = self.get_color()
        border_color = self.get_border_color()

        # --- 1. 處理底色 ---
        # 💡 檢查細節：如果顏色本質上就是完全透明 (例如長度為4且A為0)，就徹底跳過不畫底色！
        if len(color) == 4 and color[3] == 0:
            pass
        else:
            # 如果是正常顏色，我們把「顏色本身的透明度」與「外層傳入的動態 alpha」做相乘結合
            # 這樣如果按鈕本來有點半透明，套用閃爍特效時就會一起完美變淡！
            base_alpha = color[3] if len(color) == 4 else 255
            final_alpha = int(base_alpha * (alpha / 255))

            p.draw.rect(surface, (*color[:3], final_alpha), surface.get_rect(), border_radius=self.border_radius)

        # --- 2. 處理邊框 ---
        if self.border_width:
            if border_color is not None:
                # 💡 同理，邊框的透明度也要結合外層傳入的動態 alpha
                border_base_alpha = border_color[3] if len(border_color) == 4 else 255
                final_border_alpha = int(border_base_alpha * (alpha / 255))

            p.draw.rect(
                surface,
                (*border_color[:3], final_border_alpha),
                surface.get_rect(),
                border_radius=self.border_radius,
                width=self.border_width,  # 💡 傳入寬度使其變成「空心外框」
            )

        screen.blit(surface, self.draw_rect.topleft)


class TextButton(Button):
    def __init__(
        self,
        name: str,
        text: str | list,
        rect: p.Rect,
        button_color: Color,
        text_color: Color,
        font_size: int,
        # --- 以下為選填參數，有預設值 ---
        #  1. 按鈕顏色
        hover_color: Color | None = None,
        pressing_color: Color | None = None,
        disabled_color: Color | None = None,
        #  2. 文字
        hover_text: str | None = None,
        pressing_text: str | None = None,
        disable_text: str | None = None,
        #  3. 文字顏色
        hover_text_color: Color | None = None,
        pressing_text_color: Color | None = None,
        disable_text_color: Color | None = None,
        #  4. 邊框、邊框顏色
        border_radius=5,
        border_width=0,
        normal_border_color: Color | None = None,
        pressing_border_color: Color | None = None,
        hover_border_color: Color | None = None,
        disabled_border_color: Color | None = None,
        #  5. 其他
        font_type: str = "",
        r_alpha: int = 255,
        t_alpha: int = 255,
        screen_center=True,
        text_center=True,
        show=True,
        color_wave: None | list[Color] = None,
    ):
        # 1. 初始化父類別按鈕背景
        super().__init__(
            name=name,
            rect=rect,
            normal_color=button_color,
            pressing_color=pressing_color,
            hover_color=hover_color,
            disabled_color=disabled_color,
            border_width=border_width,
            border_radius=border_radius,
            show=show,
            normal_border_color=normal_border_color,
            pressing_border_color=pressing_border_color,
            hover_border_color=hover_border_color,
            disabled_border_color=disabled_border_color,
            color_wave=color_wave,
        )

        # 2. 文字內容與備份
        self.org_text = text
        self.current_text = text
        self.hover_text = hover_text if hover_text is not None else text
        self.pressing_text = pressing_text if pressing_text is not None else self.hover_text
        self.disable_text = disable_text if disable_text is not None else text

        # 3. 文字顏色與備份 (若無設定則沿用原色)
        self.org_text_color = text_color
        self.current_text_color = text_color
        self.hover_text_color = hover_text_color if hover_text_color is not None else text_color
        self.pressing_text_color = pressing_text_color if pressing_text_color is not None else self.hover_text_color
        self.disable_text_color = disable_text_color if disable_text_color is not None else text_color

        # 4. 其他屬性
        self.font_size = font_size
        self.font_type = font_type
        self.r_alpha = r_alpha
        self.t_alpha = t_alpha
        self.screen_center = screen_center
        self.text_center = text_center
        self.draw_lock = False

    def get_text_color(self):
        if not self.active:
            return self.disable_text_color
        if self.is_hoding:
            return self.pressing_text_color
        if self.is_hover:
            return self.hover_text_color
        return self.org_text_color

    def change_base_text(self, new_text: str, force=False):
        self.org_text = new_text
        self.current_text = new_text
        if force:
            self.hover_text = new_text
            self.pressing_text = new_text
            self.disable_text = new_text
        else:
            # 修改處
            self.hover_text = self.hover_text if self.hover_text is not None else new_text
            self.pressing_text = self.pressing_text if self.pressing_text is not None else self.hover_text
            self.disable_text = self.disable_text if self.disable_text is not None else new_text

    def change_base_text_color(self, new_color: Color, force=False):
        self.org_text_color = new_color
        self.current_text_color = new_color
        if force:
            self.hover_text_color = new_color
            self.pressing_text_color = new_color
            self.disable_text_color = new_color
        else:
            # 修改處
            self.hover_text_color = self.hover_text_color if self.hover_text_color is not None else new_color
            self.pressing_text_color = self.pressing_text_color if self.pressing_text_color is not None else self.hover_text_color
            self.disable_text_color = self.disable_text_color if self.disable_text_color is not None else new_color

    def update(self, events, mouse_pos: tuple[int | float]):
        super().update(events, mouse_pos)

        # 狀態優先級：Disabled > Pressed > Hover > Normal
        if not self.active:
            self.current_text = self.disable_text or self.org_text
        elif self.is_hoding:
            self.current_text = self.pressing_text or self.org_text
        elif self.is_hover:
            self.current_text = self.hover_text or self.org_text
        else:
            self.current_text = self.org_text

    # 💡 提示：讓 TextButton.draw 也能接收外部傳入的動態 alpha 特效參數
    def draw(self, screen: p.Surface, alpha=255):
        if not self.is_visible:
            return

        self.draw_rect = self.org_rect.copy()

        if self.screen_center:
            self.draw_rect.centerx = screen.get_rect().w // 2

        t_x = self.draw_rect.centerx if self.text_center else self.draw_rect.x + 10
        t_y = self.draw_rect.centery if self.text_center else self.draw_rect.y + 10

        # 1. 💡 呼叫父類別繪製背景 (底色與邊框)：把動態 alpha 傳進去
        super().draw(screen, alpha)

        # 2. 💡 結合文字的基礎透明度與動態變化的 alpha 特效
        # 這樣當特效讓按鈕變淡時，文字也會跟著一起變淡！
        final_text_alpha = int(self.t_alpha * (alpha / 255))

        # 3. 繪製文字
        show_text(
            screen,
            self.current_text,
            self.get_text_color(),
            t_x,
            t_y,
            self.font_size,
            font_type=self.font_type,
            alpha=final_text_alpha,  # 💡 關鍵細節：改用計算後的動態文字透明度
            center=True,
        )
        if self.draw_lock:
            assets.lock_rect.center = self.draw_rect.center
            # 直接在按鈕的座標附近 blit 鎖頭圖案，它就會完美跟著按鈕一起移動、滾動！
            screen.blit(assets.lock_img_surface, assets.lock_rect)


class ImageButton:
    def __init__(self, name: str, image: p.Surface, pos: list[int], screen_center=False, visible: bool = True):
        self.name = name
        self.surface = image
        self.rect = self.surface.get_rect()
        self.rect.center = pos
        self.screen_center = screen_center
        # 點擊事件屬性
        self.active = True
        self.toggle = False
        self.is_hover = False
        self.is_down = False
        self.is_hoding = False
        self.is_clicked = False

        self.is_visible = visible

    def update(self, events, mouse_pos: tuple[int | float]):
        if not self.is_visible or not self.active:
            self.is_down = False
            self.is_clicked = False
            return

        # 每幀重置（重要）
        self.is_clicked = False

        # hover
        self.is_hover = self.rect.collidepoint(mouse_pos)

        for event in events:
            # 按下
            if event.type == p.MOUSEBUTTONDOWN and event.button == 1:
                if self.is_hover:
                    self.is_down = True
                    self.is_hoding = True
            # 放開
            if event.type == p.MOUSEBUTTONUP and event.button == 1:
                self.is_hoding = False
                if self.is_down and self.is_hover:
                    self.is_clicked = True

                self.is_down = False
        if self.screen_center:
            self.rect.center = config.current_width

    def draw(self, screen: p.Surface):
        # 如果有圖片就畫圖片，沒有的話可以考慮畫個紅框作為保險
        if self.surface and self.is_visible:
            screen.blit(self.surface, self.rect)
        elif self.is_visible:
            p.draw.rect(screen, Colors.RED, self.rect)


class ImageTextButton(ImageButton):
    def __init__(
        self,
        name: str,
        image: p.Surface,
        pos: tuple[int, int],
        text: str | list,
        text_color: Color,
        size=30,
        visible: bool = True,
        center=True,
        screen_center=False,
        font_type="",
        # 文字
        hover_text: str | None = None,
        pressing_text: str | None = None,
        disable_text: str | None = None,
        # 文字顏色
        hover_text_color: Color | None = None,
        pressing_text_color: Color | None = None,
        disable_text_color: Color | None = None,
    ):
        super().__init__(name, image, pos, screen_center, visible)

        self.active = True
        self.toggle = False
        self.is_hover = False
        self.is_down = False
        self.is_hoding = False
        self.is_clicked = False

        self.font_size = size
        self.font_type = font_type
        self.text_center = center

        # 文字內容與備份
        self.org_text = text
        self.current_text = text
        self.hover_text = hover_text if hover_text is not None else text
        self.pressing_text = pressing_text if pressing_text is not None else self.hover_text
        self.disable_text = disable_text if disable_text is not None else text

        # 文字顏色與備份 (若無設定則沿用原色)
        self.org_text_color = text_color
        self.current_text_color = text_color
        self.hover_text_color = hover_text_color if hover_text_color is not None else text_color
        self.pressing_text_color = pressing_text_color if pressing_text_color is not None else self.hover_text_color
        self.disable_text_color = disable_text_color if disable_text_color is not None else text_color

    def get_text_color(self):
        if not self.active:
            return self.disable_text_color
        if self.is_hoding:
            return self.pressing_text_color
        if self.is_hover:
            return self.hover_text_color
        return self.org_text_color

    def change_base_text(self, new_text: str, force=False):
        self.org_text = new_text
        self.current_text = new_text
        if force:
            self.hover_text = new_text
            self.pressing_text = new_text
            self.disable_text = new_text
        else:
            # 修改處
            self.hover_text = self.hover_text if self.hover_text is not None else new_text
            self.pressing_text = self.pressing_text if self.pressing_text is not None else self.hover_text
            self.disable_text = self.disable_text if self.disable_text is not None else new_text

    def change_base_text_color(self, new_color: Color, force=False):
        self.org_text_color = new_color
        self.current_text_color = new_color
        if force:
            self.hover_text_color = new_color
            self.pressing_text_color = new_color
            self.disable_text_color = new_color
        else:
            # 修改處
            self.hover_text_color = self.hover_text_color if self.hover_text_color is not None else new_color
            self.pressing_text_color = self.pressing_text_color if self.pressing_text_color is not None else self.hover_text_color
            self.disable_text_color = self.disable_text_color if self.disable_text_color is not None else new_color

    def update(self, events, mouse_pos):
        super().update(events, mouse_pos)
        if self.screen_center:
            self.rect.centerx = config.current_width // 2

    def draw(self, screen):
        super().draw(screen)

        self.draw_rect = self.rect.copy()

        t_x = self.draw_rect.centerx if self.text_center else self.draw_rect.x + 10
        t_y = self.draw_rect.centery if self.text_center else self.draw_rect.y + 10

        show_text(
            screen,
            self.current_text,
            self.get_text_color(),
            t_x,
            t_y,
            size=self.font_size,
            center=self.text_center,
            screen_center=self.screen_center,
            font_type=self.font_type,
        )


def screen_vague(vague):
    """要放在此函式上的物件才會被模糊"""
    snapshot = s.copy()

    if vague > 0:
        small = p.transform.smoothscale(snapshot, (config.current_width // vague, config.current_height // vague))
        blurred = p.transform.smoothscale(small, (config.current_width, config.current_height))
        s.blit(blurred, (0, 0))

    overlay = p.Surface((config.current_width, config.current_height))
    overlay.set_alpha(150)
    overlay.fill((0, 0, 0))
    s.blit(overlay, (0, 0))


def os_open_file(pt):
    if plat.system() == "Windows":
        os.startfile(pt)
    elif plat.system() == "Darwin":
        sub.call(["open", pt])
    else:
        sub.call(["xdg-open", pt])


def clamp(start, end, num):
    if start is None:
        start = -math.inf
    if end is None:
        end = math.inf
    return min(max(start, num), end)


def in_range(start, end, num):
    # if start > end:
    #     raise RangeError("'start' can't less then 'end'")
    return start <= num <= end


collision_time = None
start_time = None
elapsed_time = 0
paused_time = 0


# 初始化
elapsed_time_ms = 0.0


def sec_timer(update=False, dt=0):
    """
    dt: 每一幀經過的真實時間 (秒)，通常由 clock.tick() 取得
    """
    global elapsed_time_ms

    if update:
        # 核心改動：真實時間差 * 你的作弊速度 = 虛擬的時間增量
        # 這樣 Timer_Speed = 2 時，時間就會跑得比現實快一倍

        import config

        elapsed_time_ms += (dt * 1000) * config.Timer_Speed

    return int(elapsed_time_ms / 1000), int(elapsed_time_ms)


def reset_timer():
    global start_time, elapsed_time_ms, paused_time
    start_time = None
    elapsed_time_ms = 0.0
    paused_time = 0


def get_direction(angle):
    """
    angle 是角度 \n
    輸入angle會回傳一組dx, dy \n
    要用兩個變數來接
    """
    a = radians(angle)
    dx = cos(a)
    dy = sin(a)
    return dx, dy


def show_time_hrs(seconds):
    """
    輸入：秒數 \n
    輸出："小時：分鐘：秒數"
    """
    hrs = seconds // 3600
    mins = seconds // 60
    sec = seconds % 60
    return f"{hrs}:" + ("0" if mins % 60 < 10 else "") + f"{mins % 60}:" + ("0" if sec < 10 else "") + f"{sec}"


def show_time_min(seconds: str | float):
    """
    輸入：秒數 \n
    輸出："分鐘：秒數"
    """
    mins = seconds // 60  # type: ignore
    sec = seconds % 60
    return f"{int(mins)}:" + ("0" if sec < 10 else "") + f"{int(sec)}"  # type: ignore


def num_to_KMBT(num):
    if num >= 1000000000000:
        text = f"{math.floor(num / 10000000000) / 100}T"
    elif num >= 1000000000:
        text = f"{math.floor(num / 10000000) / 100}B"
    elif num >= 1000000:
        text = f"{math.floor(num / 10000) / 100}M"
    elif num >= 1000:
        text = f"{math.floor(num / 10) / 100}K"
    else:
        text = f"{int(num)}"
    return text


def update_scrolling(current_y, target_y, smoth=0.1, min_val=0, max_val=None):
    # 1. 先確保目標值在合法範圍內
    if max_val is not None:
        target_y = clamp(min_val, target_y, max_val)

    # 2. 計算緩動 (Lerp 邏輯)
    if current_y != target_y and abs(target_y - current_y) > 0.1:
        current_y += (target_y - current_y) * smoth
    else:
        current_y = target_y

    # 3. 再次強制修正 current_y 確保不溢出 (這對邊界回彈很有用)
    if max_val is not None:
        current_y = clamp(min_val, current_y, max_val)

    return current_y


class FloatingText:
    """顯示往上漂浮的文字"""

    def __init__(self, text, start_x, start_y, color, size=20, time=60, speed=1.0, center=F):
        self.text = text
        # 確保文字至少離邊界 20 像素，且不超出右下角
        self.x = clamp(20, config.current_width - 60, start_x)
        self.y = clamp(20, config.current_height - 20, start_y)
        self.color = color
        self.timer = time  # 文字顯示多久
        self.max_time = time
        self.speed = speed
        self.center = center

        root = pathlib.Path(__file__).parent.resolve(strict=False)
        self.font = p.font.Font(str(root / "Ubuntu.ttf"), size)

    def update(self):
        self.y -= self.speed  # 文字慢慢往上飄
        self.timer -= 1

    def reset(self):
        self.timer = 0

    def draw(self, surface):
        if self.timer > 0:
            text_surf = self.font.render(self.text, True, self.color)

            # ✨ 建立支援透明度的暫存畫布
            temp_surf = p.Surface(text_surf.get_size(), p.SRCALPHA)
            temp_surf.blit(text_surf, (0, 0))

            # 設定透明度 (隨時間淡出)
            alpha = int((self.timer / self.max_time) * 255)
            temp_surf.set_alpha(alpha)

            # 使用 Rect 處理位置
            t_rect = temp_surf.get_rect()
            if self.center:
                t_rect.center = (int(self.x), int(self.y))
            else:
                t_rect.topleft = (int(self.x), int(self.y))

            # 邊界保護 (防止超出螢幕左側或右側)
            t_rect.left = max(10, t_rect.left)
            t_rect.right = min(config.current_width - 10, t_rect.right)

            surface.blit(temp_surf, t_rect)
