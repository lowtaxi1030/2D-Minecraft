import os

import pygame

import asset_manager
import config
import tool
import world_generator

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

player_rect = pygame.Rect(0, 0, 40, 80)

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
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        config.scroll_x -= 10
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        config.scroll_x += 10
    if keys[pygame.K_UP] or keys[pygame.K_w]:
        config.scroll_y -= 10
    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
        config.scroll_y += 10
    config.scroll_x = tool.num_range(0, 4000, config.scroll_x)
    config.scroll_y = tool.num_range(0, 1200, config.scroll_y)
    for y_idx, row in enumerate(config.world_data):
        for x_idx, block_name in enumerate(row):
            if block_name == "air":
                continue

            pixel_x = x_idx * config.BLOCK_SIZE - config.scroll_x
            pixel_y = y_idx * config.BLOCK_SIZE - config.scroll_y

            screen.blit(config.img_blocks[block_name], (pixel_x, pixel_y))

    pygame.draw.rect(screen, tool.Colors.BLUE, player_rect)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
