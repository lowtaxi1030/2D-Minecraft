from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from asset_manager import AssetManager
    from chunk_manager import ChunkManager
    from fluid_manager import FluidManager
    from player import Player
    from world_manager import World
import json
import random

import pygame

import config
import tool

world_dir = config.BASE_DIR / "saves" / config.CURRENT_WORLD / "chunks"


class Camera:
    def __init__(self, assets: AssetManager, player: Player, chunk_manager: ChunkManager):
        self.assets = assets
        self.chunk_manager = chunk_manager

        # 世界座標中的左上角
        self.scroll_x = player.hitbox.centerx
        self.scroll_y = 0

        # 螢幕震動(之後做)
        self.offset_x, self.offset_y = 0, 0

        self.shake_intensity = 0  # 最大震動幅度
        self.shake_duration = 0  # 這次震動總時間
        self.shake_elapsed = 0  # 已經震了多久(ms)

        # self.shake_strength = config.BLOCK_SIZE / 8  # px / 0.15s

        # 縮放倍率
        self.zoom = 1.0
        self._last_frame_zoom = 1.0

        # 世界中真正的方塊大小(固定)
        self.render_rect = pygame.Rect(0, 0, 0, 0)

    def shake(self, intensity: float, duration: int):
        """
        外部呼叫用\n
        duration: ms
        """
        self.shake_intensity = intensity
        self.shake_duration = duration / 1000
        self.shake_elapsed: int = 0

    def _update_shake(self, dt: int | float):
        """dt: s"""
        if self.shake_elapsed >= self.shake_duration:
            self.offset_x, self.offset_y = 0, 0
            return

        self.shake_elapsed += dt

        progress = 0
        if self.shake_elapsed > 0:
            progress = self.shake_duration / self.shake_elapsed

        strength = self.shake_intensity * (1 - progress)

        self.offset_x = random.uniform(strength, -strength)
        self.offset_y = random.uniform(strength, -strength)

    def update(self, player: Player, fluid_manager: FluidManager, dt):
        base_zoom = config.ORG_FOV / config.fov

        sprint_multiplier = config.SPRINT_ZOOM_MULTIPLIER if player.is_running else 1.0
        target_zoom = base_zoom * sprint_multiplier

        if abs(target_zoom - self.zoom) > 0.001:
            self.zoom += (target_zoom - self.zoom) * 0.1
        else:
            self.zoom = target_zoom

        view_width = config.current_width / self.zoom
        view_height = config.current_height / self.zoom

        target_scroll_x = player.hitbox.centerx - view_width / 2
        target_scroll_y = player.hitbox.centery - view_height / 2

        # max_scroll_x = config.MAP_WIDTH * config.BLOCK_SIZE - view_width
        max_scroll_y = config.MAP_HEIGHT * config.BLOCK_SIZE - view_height

        self.scroll_x = tool.update_scrolling(
            self.scroll_x,
            target_scroll_x,
            smoth=0.1,
        )

        self.scroll_y = tool.update_scrolling(
            self.scroll_y,
            target_scroll_y,
            smoth=1,
            max_val=max_scroll_y,
        )

        # self.scroll_x = tool.clamp(0, max_scroll_x, self.scroll_x)
        self.scroll_y = tool.clamp(0, max_scroll_y, self.scroll_y)

        self._update_shake(dt)

        self._load_visible_chunks(player, fluid_manager)

    def _load_visible_chunks(self, player: Player, fluid_manager: FluidManager = None):
        # 第一步：生成玩家附近的 chunk
        current_chunk = player.hitbox.centerx // (config.CHUNK_WIDTH * config.BLOCK_SIZE)

        for chunk_x in range(current_chunk - 5, current_chunk + 6):
            self.chunk_manager.get_chunk(chunk_x, fluid_manager)

        # 第二步：刪掉離玩家太遠的 chunk
        max_distance = 8

        chunk_indexes = list(self.chunk_manager.chunks.keys())
        for index in chunk_indexes:
            if abs(index - current_chunk) > max_distance:
                file_path = world_dir / f"chunk_{index}.json"
                chunk = self.chunk_manager.chunks[index]
                if chunk.is_dirty:
                    with open(file_path, 'w') as f:
                        chunk = self.chunk_manager.chunks[index]
                        json.dump(chunk.blocks, f)
                        """
                        之後可能會變成：
                        json.dump(
                            {
                            "blocks": chunk.blocks,
                            "biome": chunk.biome,
                            "version": chunk.version,
                            },
                            f,
                        )
                        """
                del self.chunk_manager.chunks[index]

    """小工具"""

    def world_to_screen(self, world_x, world_y):
        return (
            (world_x * config.BLOCK_SIZE - self.scroll_x),
            (world_y * config.BLOCK_SIZE - self.scroll_y),
        )

    def screen_to_world(self, mouse_pos):
        mouse_x = mouse_pos[0]
        mouse_y = mouse_pos[1]

        mouse_x -= self.render_rect.left
        mouse_y -= self.render_rect.top

        mouse_x /= self.zoom
        mouse_y /= self.zoom

        world_x = int((mouse_x + self.scroll_x) // config.BLOCK_SIZE)
        world_y = int((mouse_y + self.scroll_y) // config.BLOCK_SIZE)

        return (world_x, world_y)

    def visible_range(self):
        view_width = config.current_width / self.zoom
        view_height = config.current_height / self.zoom

        start_x = int(self.scroll_x // config.BLOCK_SIZE) - 3

        end_x = int((self.scroll_x + view_width) // config.BLOCK_SIZE) + 4

        start_y = tool.clamp(0, config.MAP_HEIGHT, int(self.scroll_y // config.BLOCK_SIZE) - 3)

        end_y = tool.clamp(0, config.MAP_HEIGHT, int((self.scroll_y + view_height) // config.BLOCK_SIZE) + 4)

        return start_x, end_x, start_y, end_y

    """"""

    def draw_world(self, screen: pygame.Surface, mouse_pos: tuple[int | float, int | float], world: World, draw_hover=True):
        world_x, world_y = self.screen_to_world(mouse_pos)
        start_x, end_x, start_y, end_y = self.visible_range()

        for y_pos in range(start_y, end_y):
            for x_pos in range(start_x, end_x):

                block_name = self.chunk_manager.get_block(x_pos * config.BLOCK_SIZE, y_pos * config.BLOCK_SIZE)

                pixel_x, pixel_y = self.world_to_screen(x_pos, y_pos)

                if block_name != "air":
                    # print(block_name)
                    display_block_name = world.get_block_display_name(x_pos, y_pos, block_name)
                    if block_name == "grass":
                        chunk_x = x_pos // config.CHUNK_WIDTH
                        chunk = self.chunk_manager.get_chunk(chunk_x)
                        img = self.assets.get_biome_grass(chunk.biome_name)
                    else:
                        img = self.assets.block(display_block_name)  # .get_img(block_name, "block")

                    if img:
                        screen.blit(img, (pixel_x, pixel_y))
                    else:
                        # 印出警報但讓遊戲繼續跑，這樣就算未來漏掉新方塊的圖，也不會直接 Crash！
                        print(f"⚠️ 找不到方塊圖檔：'{display_block_name}'")

                if (world_x, world_y) == (x_pos, y_pos) and draw_hover:
                    block_rect = pygame.Rect(
                        pixel_x,
                        pixel_y,
                        int(config.BLOCK_SIZE),
                        int(config.BLOCK_SIZE),
                    )
                    pygame.draw.rect(screen, tool.Colors.BLACK, block_rect, max(1, int(config.BLOCK_SIZE) // 20))

    def draw(self, screen: pygame.Surface, world_surface: pygame.Surface):
        if abs(self.zoom - self._last_frame_zoom) > 0.0005:
            scaled = pygame.transform.smoothscale(world_surface, (config.current_width, config.current_height))
        else:
            scaled = pygame.transform.scale(world_surface, (config.current_width, config.current_height))
        self._last_frame_zoom = self.zoom
        screen_rect = screen.get_rect()
        screen_rect.centerx += self.offset_x
        screen_rect.centery += self.offset_y
        self.render_rect = scaled.get_rect(center=screen_rect.center)
        screen.blit(scaled, self.render_rect)
