from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from player import Player
import json

import pygame

import asset_manager as assets
import chunk_manager
import config
import tool

world_dir = config.BASE_DIR / "saves" / config.CURRENT_WORLD / "chunks"


class Camera:
    def __init__(self):
        # 世界座標中的左上角
        self.scroll_x = 0
        self.scroll_y = 0

        # 縮放倍率
        self.zoom = 1.0

        # 世界中真正的方塊大小(固定)
        self.block_size = config.BLOCK_SIZE
        self.render_rect = pygame.Rect(0, 0, 0, 0)

    def update(self, player: "Player"):

        view_width = config.current_width / self.zoom
        view_height = config.current_height / self.zoom

        target_scroll_x = player.rect.centerx - view_width / 2
        target_scroll_y = player.rect.centery - view_height / 2

        # max_scroll_x = config.MAP_WIDTH * self.block_size - view_width
        max_scroll_y = config.MAP_HEIGHT * self.block_size - view_height

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

        self._load_visible_chunks(player)

    def _load_visible_chunks(self, player: "Player"):
        # 第一步：生成玩家附近的 chunk
        current_chunk = player.rect.centerx // (config.CHUNK_WIDTH * config.BLOCK_SIZE)

        for chunk_x in range(current_chunk - 5, current_chunk + 6):
            chunk_manager.get_chunk(chunk_x)

        # 第二步：刪掉離玩家太遠的 chunk
        max_distance = 8

        chunk_indexes = list(config.chunks.keys())
        for index in chunk_indexes:
            if abs(index - current_chunk) > max_distance:
                file_path = world_dir / f"chunk_{index}.json"
                chunk = config.chunks[index]
                if chunk.is_dirty:
                    with open(file_path, 'w') as f:
                        chunk = config.chunks[index]
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
                del config.chunks[index]

    """小工具"""

    def world_to_screen(self, world_x, world_y):
        return (
            world_x * self.block_size - self.scroll_x,
            world_y * self.block_size - self.scroll_y,
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

        start_x = int(self.scroll_x // config.BLOCK_SIZE) - 1

        end_x = int((self.scroll_x + view_width) // config.BLOCK_SIZE) + 2

        start_y = int(self.scroll_y // config.BLOCK_SIZE) - 1

        end_y = int((self.scroll_y + view_height) // config.BLOCK_SIZE) + 2

        return start_x, end_x, start_y, end_y

    """"""

    def draw_world(self, screen: pygame.Surface, mouse_pos: tuple[int | float, int | float], draw_hover=True):
        world_x, world_y = self.screen_to_world(mouse_pos)
        start_x, end_x, start_y, end_y = self.visible_range()

        for y_pos in range(start_y, end_y):
            for x_pos in range(start_x, end_x):

                block_name = chunk_manager.get_block(x_pos * config.BLOCK_SIZE, y_pos * config.BLOCK_SIZE)

                pixel_x, pixel_y = self.world_to_screen(x_pos, y_pos)

                if block_name != "air":
                    screen.blit(assets.img_blocks[block_name], (pixel_x, pixel_y))

                if (world_x, world_y) == (x_pos, y_pos) and draw_hover:
                    block_rect = pygame.Rect(
                        pixel_x,
                        pixel_y,
                        int(config.BLOCK_SIZE),
                        int(config.BLOCK_SIZE),
                    )
                    pygame.draw.rect(screen, tool.Colors.BLACK, block_rect, max(1, int(config.BLOCK_SIZE) // 20))

    def draw(self, screen, world_surface):
        scaled = pygame.transform.scale_by(world_surface, self.zoom)

        self.render_rect = scaled.get_rect(center=screen.get_rect().center)

        screen.blit(scaled, self.render_rect)

    def draw_option_bg(self, player, mouse_pos, screen, world_surface):
        world_surface.fill(tool.Colors.CYAN)

        self.update(player)
        player.draw(world_surface, self.scroll_x, self.scroll_y)
        self.draw_world(world_surface, mouse_pos, draw_hover=False)
        self.draw(screen, world_surface)
