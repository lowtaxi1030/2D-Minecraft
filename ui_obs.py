from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum

import pygame


class BaseUI:
    def __init__(self, name: str, rect: pygame.Rect, interactive: Interactive | None = None):
        self.name = name
        self.rect = rect
        self.is_visible = True
        self.alpha = 255

        self.interactive = interactive
        self.visuals: list[Visual] = []

    def update(self, mouse_pos: tuple[int, int], mouse_buttons: tuple[bool, bool, bool]):
        if self.interactive:
            self.interactive.update(self.rect.collidepoint(mouse_pos), mouse_pos, mouse_buttons)

    def draw(self, screen: pygame.Surface):
        state = self.interactive.visual_state if self.interactive else "normal"
        for visual in self.visuals:
            visual.draw(screen, self.rect, state, self.alpha if self.interactive else 255)


class ColorState:
    def __init__(self, normal: pygame.Color, hover: pygame.Color, pressed: pygame.Color, disabled: pygame.Color = None):
        self.normal = normal
        self.hover = hover
        self.pressed = pressed
        self.disabled = disabled

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


class InteractionMode(Enum):
    CLICK = "click"
    HOVER = "hover"
    DRAG = "drag"
    TOGGLE = "toggle"


class InteractionBehavior(ABC):
    @abstractmethod
    def apply(self, interactive: Interactive, hover, mouse_pos, mouse_buttons):
        pass


class ClickBehavior(InteractionBehavior):
    def apply(self, interactive: Interactive, hover, mouse_pos, mouse_buttons):
        interactive.hover = hover
        interactive.down = mouse_buttons[0] and interactive.hover
        interactive.clicked = False
        if interactive.down:
            interactive.holding = True
        elif not mouse_buttons[0] and interactive.holding:
            interactive.clicked = True
            interactive.holding = False


class HoverBehavior(InteractionBehavior):
    def apply(self, interactive: Interactive, hover, mouse_pos, mouse_buttons):
        interactive.hover = hover


class DragBehavior(InteractionBehavior):
    def apply(self, interactive: Interactive, hover, mouse_pos, mouse_buttons):
        interactive.hover = hover
        interactive.down = mouse_buttons[0] and interactive.hover
        if interactive.down:
            interactive.dragging = True
            interactive.last_mouse_pos = mouse_pos
        elif not mouse_buttons[0]:
            interactive.dragging = False


class ToggleBehavior(InteractionBehavior):
    def apply(self, interactive: Interactive, hover, mouse_pos, mouse_buttons):
        interactive.hover = hover
        interactive.down = mouse_buttons[0] and interactive.hover
        interactive.clicked = False
        if interactive.down:
            interactive.holding = True
        elif not mouse_buttons[0] and interactive.holding:
            interactive.clicked = True
            interactive.toggle = not interactive.toggle


interactive_behavior_map = {
    InteractionMode.CLICK: ClickBehavior(),
    InteractionMode.HOVER: HoverBehavior(),
    InteractionMode.DRAG: DragBehavior(),
    InteractionMode.TOGGLE: ToggleBehavior(),
}


class Interactive:

    def __init__(self, ui_type: InteractionMode):
        self.active = False
        self.hover = False
        self.down = False
        self.holding = False
        self.dragging = False
        self.clicked = False
        self.toggle = False
        self.type = ui_type
        self.last_mouse_pos = (0, 0)

        self.behavior = interactive_behavior_map[self.type]

    def update(self, hover: bool, mouse_pos: tuple[int, int], mouse_buttons: tuple[bool, bool, bool]):
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


class Visual(ABC):
    @abstractmethod
    def draw(self, screen: pygame.Surface, rect: pygame.Rect, state, alpha):
        pass


class RectVisual: ...


class ImageVisual: ...


class TextVisual: ...
