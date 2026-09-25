from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:

    from asset_manager import AssetManager

import pygame

import config
import tool
import ui.element.ui_core as ui_core

from .ui_core import BaseUI, ImageVisual, InteractionMode, Interactive, RectVisual, StateGroup, TextVisual


class TextOwnerMixin:
    text_visual: TextVisual
    shadow_visual: TextVisual | None

    @property
    def text(self):
        return self.text_visual.text

    @text.setter
    def text(self, value):
        self.text_visual.text.set_normal(value)
        if self.shadow_visual is not None:
            self.shadow_visual.text.set_normal(value)


def _init_text_visual(
    ui_ob: Text | TextButton | ImageTextButton,
    text,
    size,
    colors,
    on_text,
    on_colors,
    font_type,
    screen_center,
    shadow,
    shadow_offset,
):

    ui_ob.shadow_visual = None
    if shadow:
        ui_ob.shadow_visual = TextVisual(
            text=text,
            size=size,
            colors=tool.Colors.BLACK,
            on_text=on_text,
            on_colors=tool.Colors.BLACK,
            font_type=font_type,
            screen_center=screen_center,
            is_shadow=True,
            shadow_offset=shadow_offset,
        )
        ui_ob.visuals.append(ui_ob.shadow_visual)

    ui_ob.text_visual = TextVisual(
        text=text,
        size=size,
        colors=colors,
        on_text=on_text,
        on_colors=on_colors,
        font_type=font_type,
        screen_center=screen_center,
    )
    ui_ob.visuals.append(ui_ob.text_visual)


class Text(BaseUI, TextOwnerMixin):
    def __init__(
        self,
        name: str,
        text: StateGroup[str | list] | str | list,
        pos: config.Pos,
        colors: StateGroup[pygame.Color] | pygame.Color | tuple[int, int, int],
        size: int = 24,
        on_text: StateGroup[str] | None = None,
        on_colors: StateGroup[pygame.Color] | None = None,
        font_type: str | None = "Minecraft",
        screen_center: bool = False,
        *,
        shadow: bool = True,
        shadow_offset: tuple[int, int] = (2, 2),
        interaction_mode: InteractionMode | None = InteractionMode.CLICK,
    ):
        font = ui_core.get_font(font_type, size)

        sizes = [ui_core.get_biggest_text_size(font, t) for t in [text, on_text] if t is not None]

        max_width = max((width for width, _ in sizes), default=0)
        max_height = max((height for _, height in sizes), default=0)

        rect = pygame.Rect(0, 0, max_width, max_height)
        rect.center = pos

        interactive = Interactive(interaction_mode) if interaction_mode is not None else None
        super().__init__(name, rect, interactive)

        _init_text_visual(
            ui_ob=self,
            text=text,
            size=size,
            colors=colors,
            on_text=on_text,
            on_colors=on_colors,
            screen_center=screen_center,
            shadow=shadow,
            shadow_offset=shadow_offset,
            font_type=font_type,
        )


class Button(BaseUI):
    def __init__(
        self,
        name: str,
        rect: pygame.Rect,
        colors: StateGroup[pygame.Color] | pygame.Color | tuple[int, int, int],
        on_colors: StateGroup[pygame.Color] | pygame.Color | tuple[int, int, int] | None = None,
        *,
        interaction_mode: InteractionMode | None = InteractionMode.CLICK,
    ):
        interactive = Interactive(interaction_mode) if interaction_mode is not None else None
        super().__init__(name, rect, interactive)
        self.rect_visual = RectVisual(colors, on_colors)

        self.visuals.append(self.rect_visual)

    def chage_color(self, new_color, target: str | None = None, force=False):
        if target is None or target == "normal":
            self.rect_visual.colors.set_normal(new_color, force)


class TextButton(Button, TextOwnerMixin):
    def __init__(
        self,
        name: str,
        text: StateGroup[str | list] | str | list,
        rect: pygame.Rect,
        text_colors: StateGroup[pygame.Color] | pygame.Color | tuple[int, int, int],
        rect_colors: StateGroup[pygame.Color] | pygame.Color | tuple[int, int, int],
        size: int = 24,
        on_text: StateGroup[str] | None = None,
        text_on_colors: StateGroup[pygame.Color] | None = None,
        rect_on_colors: StateGroup[pygame.Color] | None = None,
        font_type: str | None = "Minecraft",
        screen_center: bool = False,
        *,
        shadow: bool = True,
        shadow_offset: tuple[int, int] = (2, 2),
        interaction_mode: InteractionMode | None = InteractionMode.CLICK,
    ):
        super().__init__(
            name=name,
            rect=rect,
            colors=rect_colors,
            on_colors=rect_on_colors,
            interaction_mode=interaction_mode,
        )

        _init_text_visual(
            ui_ob=self,
            text=text,
            size=size,
            colors=text_colors,
            on_text=on_text,
            on_colors=text_on_colors,
            screen_center=screen_center,
            shadow=shadow,
            shadow_offset=shadow_offset,
            font_type=font_type,
        )


class ImageButton(BaseUI):
    def __init__(
        self,
        name: str,
        image: pygame.Surface,
        pos: tuple[int, int],
        *,
        interaction_mode: InteractionMode | None = InteractionMode.CLICK,
    ):
        self.surface = image
        interactive = Interactive(interaction_mode) if interaction_mode is not None else None
        super().__init__(name, self.surface.get_rect(), interactive)
        self.rect.center = pos
        self.image_visual = ImageVisual(image)

        self.visuals.append(self.image_visual)


class ImageTextButton(ImageButton, TextOwnerMixin):
    def __init__(
        self,
        name: str,
        text: StateGroup[str | list] | str | list,
        image: pygame.Surface,
        pos: tuple[int, int],
        text_colors: StateGroup[pygame.Color] | pygame.Color | tuple[int, int, int],
        size: int = 24,
        on_text: StateGroup[str] | None = None,
        text_on_colors: StateGroup[pygame.Color] | None = None,
        font_type: str | None = "Minecraft",
        screen_center: bool = False,
        *,
        shadow: bool = True,
        shadow_offset: tuple[int, int] = (2, 2),
        interaction_mode: InteractionMode | None = InteractionMode.CLICK,
    ):
        super().__init__(name=name, image=image, pos=pos, interaction_mode=interaction_mode)

        _init_text_visual(
            ui_ob=self,
            text=text,
            size=size,
            colors=text_colors,
            on_text=on_text,
            on_colors=text_on_colors,
            screen_center=screen_center,
            shadow=shadow,
            shadow_offset=shadow_offset,
            font_type=font_type,
        )


item_uis: dict[str, ImageTextButton] = {}


def draw_item(screen: pygame.Surface, assets: AssetManager, item, center_x, center_y):
    block_img = assets.block(item["type"])
    block_img = pygame.transform.scale(block_img, (48, 48))
    block_rect = block_img.get_rect()
    block_rect.center = (center_x, center_y)
    show_center_x = center_x - 5
    if item["count"] < 10:
        show_center_x = center_x + 11

    cache_key = f"{item["type"]}_{item["count"]}"

    if not item_uis.get(cache_key):
        item_uis[cache_key] = ImageTextButton(
            name=cache_key,
            text=str(item["count"]),
            image=block_img,
            pos=(show_center_x, center_y + 5),
            text_colors=tool.Colors.WHITE,
            size=25,
            show=item["count"] > 1,
        )

    item_uis[cache_key].draw(screen)
