import pygame

import asset_manager as assets
import config
import tool


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

    def update(self, player):

        view_width = config.current_width / self.zoom
        view_height = config.current_height / self.zoom

        target_scroll_x = player.rect.centerx - view_width / 2
        target_scroll_y = player.rect.centery - view_height / 2

        max_scroll_x = config.MAP_WIDTH * self.block_size - view_width
        max_scroll_y = config.MAP_HEIGHT * self.block_size - view_height

        self.scroll_x = tool.update_scrolling(
            self.scroll_x,
            target_scroll_x,
            smoth=0.1,
            max_val=max_scroll_x,
        )

        self.scroll_y = tool.update_scrolling(
            self.scroll_y,
            target_scroll_y,
            smoth=1,
            max_val=max_scroll_y,
        )

        self.scroll_x = tool.clamp(0, max_scroll_x, self.scroll_x)
        self.scroll_y = tool.clamp(0, max_scroll_y, self.scroll_y)

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

        return (
            tool.clamp(0, config.MAP_WIDTH - 1, world_x),
            tool.clamp(0, config.MAP_HEIGHT - 1, world_y),
        )

    def visible_range(self):
        view_width = config.current_width / self.zoom
        view_height = config.current_height / self.zoom

        start_x = max(0, int(self.scroll_x // config.BLOCK_SIZE) - 2)

        end_x = min(
            config.MAP_WIDTH,
            int((self.scroll_x + view_width) // config.BLOCK_SIZE) + 2,
        )

        start_y = max(0, int(self.scroll_y // config.BLOCK_SIZE) - 2)

        end_y = min(
            config.MAP_HEIGHT,
            int((self.scroll_y + view_height) // config.BLOCK_SIZE) + 2,
        )

        return start_x, end_x, start_y, end_y

    """"""

    def draw_world(self, screen: pygame.Surface, mouse_pos: tuple[int | float, int | float], draw_hover=True):
        world_x, world_y = self.screen_to_world(mouse_pos)
        start_x, end_x, start_y, end_y = self.visible_range()

        for y_pos in range(start_y, end_y):
            for x_pos in range(start_x, end_x):

                block_name = config.world_data[y_pos][x_pos]

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

