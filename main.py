import os

import pygame

import asset_manager
import config
import tool
import world_generator
from player import Player

# 告訴系統將下一個建立的視窗放在螢幕正中央
os.environ['SDL_VIDEO_CENTERED'] = '1'

pygame.init()
screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT), pygame.RESIZABLE)
running = True
clock = pygame.time.Clock()
screen_text = "2D Minecraft - V0.0.0"
pygame.display.set_caption(screen_text)

config.img_blocks = asset_manager.load_all_blocks()

config.world_data = world_generator.make_map(config.MAP_WIDHT, config.MAP_HEIGHT)

player = Player(100, 0)

while running:
    screen.fill(tool.Colors.CYAN)
    events = pygame.event.get()
    keys = pygame.key.get_pressed()
    for event in events:
        if event.type == pygame.VIDEORESIZE:
            new_widht = tool.num_range(300, 1400, event.w)
            new_height = tool.num_range(200, 800, event.h)
            screen = pygame.display.set_mode((new_widht, new_height), pygame.RESIZABLE)
        if event.type == pygame.QUIT:
            running = False
    for y_idx, row in enumerate(config.world_data):
        for x_idx, block_name in enumerate(row):
            if block_name == "air":
                continue

            pixel_x = x_idx * config.BLOCK_SIZE - config.scroll_x
            pixel_y = y_idx * config.BLOCK_SIZE - config.scroll_y

            screen.blit(config.img_blocks[block_name], (pixel_x, pixel_y))

    player.handle_input()
    player.update(config.world_data)
    player.draw(screen, config.scroll_x, config.scroll_y)

    # 畫面捲動
    target_scroll_x = player.rect.centerx - (config.WIDTH // 2)
    target_scroll_y = player.rect.centery - (config.HEIGHT // 2)

    # 3. 加上你原本就很厲害的緩動或範圍限制 (利用你寫好的 tool.num_range)
    config.scroll_x = tool.num_range(0, 3000, target_scroll_x)
    config.scroll_y = tool.num_range(0, 1200, target_scroll_y)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
