from __future__ import annotations

import typing

# if TYPE_CHECKING:
#     pass
from abc import ABC, abstractmethod
from enum import Enum

import pygame

import config


class BaseUI:
    def __init__(self, name: str, rect: pygame.Rect, interactive: Interactive | None = None):
        self.name = name
        self.rect = rect
        self.is_visible = True
        self.alpha = 255

        self.interactive = interactive
        self.visuals: list[Visual] = []

    @property
    def is_clicked(self):
        if self.interactive is not None:
            return self.interactive.clicked
        return False

    def update(self, mouse_pos: tuple[int, int], mouse_buttons: tuple[bool, bool, bool]):
        if self.interactive:
            self.interactive.update(self.rect.collidepoint(mouse_pos), mouse_pos, mouse_buttons)

    def draw(self, screen: pygame.Surface):
        state = self.interactive.visual_state if self.interactive else "normal"
        for visual in self.visuals:
            visual.draw(
                screen,
                self.rect,
                state,
                self.alpha,
                self.interactive.toggle if self.interactive else False,
            )


T = typing.TypeVar("T")


class StateGroup(typing.Generic[T]):
    def __init__(
        self,
        normal: T,
        hover: T = None,
        pressed: T = None,
        disabled: T = None,
    ):
        self._explicit: dict[str, bool] = {
            "hover": hover is not None,
            "pressed": pressed is not None,
            "disabled": disabled is not None,
        }

        self.normal = normal
        self.hover = hover if hover is not None else self.normal
        self.pressed = pressed if pressed is not None else self.hover
        self.disabled = disabled if disabled is not None else self.pressed

    def resolve(self, state):
        if state == "normal":
            return self.normal
        elif state == "hover":
            return self.hover
        elif state == "pressed":
            return self.pressed
        elif state == "disabled":
            return self.disabled
        else:
            raise ValueError(f"Invalid state: {state}")

    def set_normal(self, new_value: T, force: bool = False):
        self.normal = new_value
        if force:
            self.hover = new_value
            self.pressed = new_value
            self.disabled = new_value

            for key in ["hover", "pressed", "disabled"]:
                self._explicit[key] = False
        else:
            if not self._explicit["hover"]:
                self.hover = self.normal
            if not self._explicit["pressed"]:
                self.pressed = self.hover
            if not self._explicit["disabled"]:
                self.disabled = self.pressed

    def __iter__(self):
        yield from [self.normal, self.hover, self.pressed, self.disabled]


class InteractionMode(Enum):
    CLICK = "click"
    HOVER = "hover"
    DRAG = "drag"
    TOGGLE = "toggle"


class InteractionBehavior(ABC):
    @abstractmethod
    def apply(self, interactive: Interactive, hover, mouse_pos, mouse_buttons):
        pass


"""Behaviors"""


class ClickBehavior(InteractionBehavior):
    def apply(self, interactive: Interactive, hover, mouse_pos, mouse_buttons):
        interactive.clicked = False
        just_pressed = mouse_buttons[0] and not interactive.was_down  # 這一幀才剛按下去
        interactive.hover = hover
        interactive.down = mouse_buttons[0] and interactive.hover

        if just_pressed and interactive.hover:
            interactive.holding = True
        elif not mouse_buttons[0] and interactive.holding:
            if interactive.hover:
                interactive.clicked = True
            interactive.holding = False

        interactive.was_down = mouse_buttons[0]  # 幫下一幀記錄這一幀的狀態，要放在最後


class HoverBehavior(InteractionBehavior):
    def apply(self, interactive: Interactive, hover, mouse_pos, mouse_buttons):
        interactive.hover = hover


class DragBehavior(InteractionBehavior):
    def apply(self, interactive: Interactive, hover, mouse_pos, mouse_buttons):
        just_pressed = mouse_buttons[0] and not interactive.was_down  # 這一幀才剛按下去
        interactive.hover = hover
        interactive.down = mouse_buttons[0] and interactive.hover

        if just_pressed and interactive.hover:
            interactive.dragging = True
            interactive.last_mouse_pos = mouse_pos
        elif not mouse_buttons[0] and interactive.dragging:
            interactive.dragging = False

        interactive.was_down = mouse_buttons[0]


class ToggleBehavior(InteractionBehavior):
    def apply(self, interactive: Interactive, hover, mouse_pos, mouse_buttons):
        interactive.clicked = False
        just_pressed = mouse_buttons[0] and not interactive.was_down  # 這一幀才剛按下去
        interactive.hover = hover
        interactive.down = mouse_buttons[0] and interactive.hover

        if just_pressed and interactive.hover:
            interactive.holding = True
        elif not mouse_buttons[0] and interactive.holding:
            if interactive.hover:
                interactive.clicked = True
                interactive.toggle = not interactive.toggle
            interactive.holding = False

        interactive.was_down = mouse_buttons[0]


""""""


interactive_behavior_map = {
    InteractionMode.CLICK: ClickBehavior(),
    InteractionMode.HOVER: HoverBehavior(),
    InteractionMode.DRAG: DragBehavior(),
    InteractionMode.TOGGLE: ToggleBehavior(),
}


class Interactive:

    def __init__(self, ui_type: InteractionMode):
        self.active = True
        self.hover = False
        self.down = False
        self.was_down = False
        self.holding = False
        self.dragging = False
        self.clicked = False
        self.toggle = False
        self.type = ui_type
        self.last_mouse_pos = (0, 0)

        self.behavior = interactive_behavior_map[self.type]

    def update(
        self,
        hover: bool,
        mouse_pos: tuple[int, int],
        mouse_buttons: tuple[bool, bool, bool],
    ):
        if self.active:
            self.behavior.apply(self, hover, mouse_pos, mouse_buttons)

    @property
    def visual_state(self):
        if not self.active:
            return "disabled"
        elif self.holding or self.dragging:
            return "pressed"
        elif self.hover:
            return "hover"
        else:
            return "normal"


def as_state_group(value, none_ok=False):
    if none_ok and value is None:
        return None
    return value if isinstance(value, StateGroup) else StateGroup(value)


class Visual(ABC):
    @abstractmethod
    def draw(
        self,
        screen: pygame.Surface,
        rect: pygame.Rect,
        state: str,
        alpha,
        toggle: bool = False,
    ):
        pass


class RectVisual(Visual):
    def __init__(
        self,
        colors: StateGroup[pygame.Color] | pygame.Color | tuple[int, int, int],
        on_colors: StateGroup[pygame.Color] | pygame.Color | tuple[int, int, int] | None = None,
    ):
        """
        colors: 給不需要 toggle 的一般按鈕用，或當作 toggle 情境下的「關」色盤\n
        on_colors: 如果不傳或傳 None 就視為'不支援 toggle 的UI'
        """
        self.colors = as_state_group(colors)
        self.on_colors = as_state_group(on_colors, none_ok=True)

    def draw(self, screen: pygame.Surface, rect: pygame.Rect, state, alpha, toggle=False):
        if self.on_colors is not None and toggle:
            current_color_state = self.on_colors
        else:
            current_color_state = self.colors
        current_color = current_color_state.resolve(state)
        render_rect = pygame.Surface(rect.size, pygame.SRCALPHA)
        render_rect.set_alpha(alpha)
        pygame.draw.rect(render_rect, current_color, render_rect.get_rect())
        screen.blit(render_rect, rect.topleft)


class ImageVisual(Visual):
    def __init__(self, image: pygame.Surface):
        self.image = image.copy()

    def draw(self, screen: pygame.Surface, rect: pygame.Rect, state, alpha, toggle=False):
        self.image.set_alpha(alpha)
        screen.blit(self.image, rect.topleft)


font_cache = {}
text_cache = {}


def get_font(font_type, size):
    # 決定路徑
    if font_type is not None:
        resolved_path = config.BASE_DIR / f"{font_type}.ttf"
    else:
        resolved_path = None

    # 快取
    cache_key = (resolved_path, size)
    if font := font_cache.get(cache_key):
        pass
    else:
        font = pygame.font.Font(resolved_path, size)
        font_cache[cache_key] = font

    return font


def get_biggest_text_size(font: pygame.Font, text: StateGroup[str | list] | str | list):
    # if text is None:
    #     return (0, 0)
    text_group = as_state_group(text)
    max_width, max_height = 0, 0
    for text_state in text_group:
        if isinstance(text_state, list):
            height = 0
            for line in text_state:
                max_width = max((size := font.size(line))[0], max_width)
                height += size[1]
            max_height = max(height, max_height)
        elif isinstance(text_state, str):
            size = font.size(text_state)
            max_width = max(size[0], max_width)
            max_height = max(size[1], max_height)
    return max_width, max_height


class TextVisual(Visual):
    def __init__(
        self,
        text: StateGroup[str | list] | str | list,
        size: int,
        colors: StateGroup[pygame.Color] | pygame.Color | tuple[int, int, int],
        on_text: StateGroup[str] | str | None = None,
        on_colors: StateGroup[pygame.Color] | pygame.Color | None = None,
        font_type: str | None = "Minecraft3",
        *,
        screen_center: bool = False,
        is_shadow: bool = False,
        shadow_offset: tuple[int, int] = (2, 2),
    ):
        """
        文字顯示\n
        colors: 給不需要 toggle 的一般按鈕用，或當作 toggle 情境下的「關」色盤\n
        on_colors: 如果不傳或傳 None 就視為'不支援 toggle 的UI'\n
        font_type: 請確保 font_type 跟目標 .ttf 的檔名一致，因為初始化會直接組合 f'{font_type}.ttf'。還有，預設字型可以依據最常用的字型修改
        """

        self.font = get_font(font_type, size)

        self.text = as_state_group(text)
        self.on_text = as_state_group(on_text, none_ok=True)
        self.colors = as_state_group(colors)
        self.on_colors = as_state_group(on_colors, none_ok=True)

        self.screen_center = screen_center
        self.is_shadow = is_shadow
        self.shadow_offset = shadow_offset

    def draw(self, screen: pygame.Surface, rect: pygame.Rect, state: str, alpha, toggle=False):
        # 決定顏色
        if self.on_colors is not None and toggle:
            current_color_state = self.on_colors
        else:
            current_color_state = self.colors

        current_color = current_color_state.resolve(state)

        # 決定文字
        if self.on_text is not None and toggle:
            current_text_state = self.on_text
        else:
            current_text_state = self.text

        current_text = current_text_state.resolve(state)

        # 多行文字渲染
        text_list = current_text if isinstance(current_text, list) else [current_text]

        for text in text_list:
            cache_key = (
                (text, current_color, alpha, "shadow") if self.is_shadow else (text, current_color, alpha)
            )  # 加上標籤避免跟主要文字快取衝突
            if cache_key in text_cache:
                render_text = text_cache[cache_key]
            else:
                render_text = self.font.render(text, True, current_color)
                render_text.set_alpha(alpha)
                text_cache[cache_key] = render_text
                if len(text_cache) > 300:
                    text_cache.clear()
            text_rect = render_text.get_rect(center=rect.center)
            if self.is_shadow:
                text_rect.move_ip(*self.shadow_offset)

            if self.screen_center:
                text_rect.centerx = config.current_width // 2
            screen.blit(render_text, text_rect)
