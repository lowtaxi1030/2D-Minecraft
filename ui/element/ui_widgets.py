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


def _init_text_visual(ui_ob: Text | TextButton | ImageTextButton, *, shadow, shadow_offset, **text_visual_kwargs):
    ui_ob.shadow_visual = None

    if shadow:
        shadow_kwargs = text_visual_kwargs.copy()

        shadow_kwargs["colors"] = tool.Colors.BLACK
        shadow_kwargs["on_colors"] = tool.Colors.BLACK
        shadow_kwargs["is_shadow"] = True
        shadow_kwargs["shadow_offset"] = shadow_offset

        ui_ob.shadow_visual = TextVisual(**shadow_kwargs)
        ui_ob.visuals.append(ui_ob.shadow_visual)

    ui_ob.text_visual = TextVisual(**text_visual_kwargs)
    ui_ob.visuals.append(ui_ob.text_visual)


def replace_rect(target_rect: pygame.Rect, pos: config.Pos, anchor_mode: str) -> config.Pos:
    if anchor_mode == "topleft":
        target_rect.topleft = pos
    elif anchor_mode == "topright":
        target_rect.topright = pos
    else:
        target_rect.center = pos


def _resize_rect(font, text, on_text, anchor_pos: config.Pos, anchor_mode: str, line_gap):
    sizes = [ui_core.get_biggest_text_size(font, t, line_gap) for t in [text, on_text] if t is not None]
    max_width = max((width for width, _ in sizes), default=0)
    max_height = max((height for _, height in sizes), default=0)

    rect = pygame.Rect(0, 0, max_width, max_height)

    replace_rect(rect, anchor_pos, anchor_mode)

    return rect


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
        font_type: str | None = ui_core.DEFAULT_FONT,
        screen_center: bool = False,
        *,
        line_gap: int = 5,
        anchor: str = "center",
        align: str = "center",
        shadow: bool = True,
        shadow_offset: tuple[int, int] = (2, 2),
        show: bool = True,
        interaction_mode: InteractionMode | None = InteractionMode.CLICK,
    ):

        self._font = ui_core.get_font(font_type, size)

        self._anchor_pos = pos
        self._anchor_mode = anchor

        self._line_gap = line_gap

        interactive = Interactive(interaction_mode) if interaction_mode is not None else None
        super().__init__(
            name,
            _resize_rect(
                font=self._font,
                text=text,
                on_text=on_text,
                anchor_pos=self._anchor_pos,
                anchor_mode=self._anchor_mode,
                line_gap=self._line_gap,
            ),
            interactive,
        )

        self.show = show

        _init_text_visual(
            ui_ob=self,
            text=text,
            size=size,
            colors=colors,
            on_text=on_text,
            on_colors=on_colors,
            align=align,
            line_gap=line_gap,
            screen_center=screen_center,
            shadow=shadow,
            shadow_offset=shadow_offset,
            font_type=font_type,
        )

    @property
    def pos(self):
        return self._anchor_pos

    @pos.setter
    def pos(self, value: config.Pos):
        self._anchor_pos = value
        replace_rect(self.rect, value, self._anchor_mode)

    @property
    def text(self):
        return self.text_visual.text

    @text.setter
    def text(self, value):
        TextOwnerMixin.text.fset(self, value)
        self.rect = _resize_rect(
            self._font, self.text_visual.text, self.text_visual.on_text, self._anchor_pos, self._anchor_mode, self._line_gap
        )

    def draw(self, screen):
        if self.show:
            super().draw(screen)


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
        font_type: str | None = ui_core.DEFAULT_FONT,
        screen_center: bool = False,
        *,
        text_align: str = "center",
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
            align=text_align,
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
        font_type: str | None = ui_core.DEFAULT_FONT,
        screen_center: bool = False,
        *,
        text_align: str = "center",
        shadow: bool = True,
        shadow_offset: tuple[int, int] = (2, 2),
        show: bool = True,
        interaction_mode: InteractionMode | None = InteractionMode.CLICK,
    ):
        super().__init__(name=name, image=image, pos=pos, interaction_mode=interaction_mode)

        self.show = show

        _init_text_visual(
            ui_ob=self,
            text=text,
            size=size,
            colors=text_colors,
            on_text=on_text,
            on_colors=text_on_colors,
            align=text_align,
            screen_center=screen_center,
            shadow=shadow,
            shadow_offset=shadow_offset,
            font_type=font_type,
        )

    def draw(self, screen):
        if self.show:
            super().draw(screen)


item_uis: dict[tuple[str | int, tuple[int, int]], ImageButton | Text] = {}


def draw_item(screen: pygame.Surface, assets: AssetManager, item: config.Item, center_x, center_y):
    count_show_x = center_x + 28

    block_pos = (center_x + 1, center_y)

    block_cache_key = (item["type"], block_pos)
    if not item_uis.get(block_cache_key):
        block_img = assets.block(item["type"])
        block_img = pygame.transform.scale(block_img, (48, 48))
        item_uis[block_cache_key] = ImageButton(
            name=str(block_cache_key),
            image=block_img,
            pos=block_pos,
            interaction_mode=None,
        )

    count_cache_key = (item["count"], (count_show_x, center_y + 5))
    if not item_uis.get(count_cache_key):
        item_uis[count_cache_key] = Text(
            name=str(count_cache_key),
            pos=(count_show_x, center_y + 5),
            text=str(item["count"]),
            colors=tool.Colors.WHITE,
            size=25,
            show=item["count"] > 1,
            anchor="topright",
            interaction_mode=None,
        )

    item_uis[block_cache_key].draw(screen)
    item_uis[count_cache_key].draw(screen)
