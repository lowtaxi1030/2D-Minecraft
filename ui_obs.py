import pathlib

import pygame as p

import asset_manager as assets
import config
from tool import Colors

Color = tuple[int, int, int]
AlphaColor = tuple[int, int, int, int]

text_cache = {}

root = pathlib.Path(__file__).parent.resolve(strict=False)

# defult_font = p.font.Font(str(root / "Minecraft.ttf"), 24)


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
            font = p.font.Font(str(root / "Minecraft3.ttf"), size)
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
