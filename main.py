import os

import pygame

import asset_manager as assets
import config
import tool
import ui_manager
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

config.img_blocks = assets.load_all_blocks()
config.world_data = world_generator.make_map(config.MAP_WIDTH, config.MAP_HEIGHT)
player = Player(100, 0)

ui = ui_manager.UI()

while running:
    screen.fill(tool.Colors.CYAN)
    events = pygame.event.get()
    keys = pygame.key.get_pressed()
    mouse_buttons = pygame.mouse.get_pressed()
    for event in events:
        if event.type == pygame.VIDEORESIZE:
            config.current_width = event.w
            config.current_height = event.h
            # screen = pygame.display.set_mode((config.current_width, config.current_height), pygame.RESIZABLE)
            screen = pygame.display.set_mode((event.w, event.h), screen.get_flags())
        if event.type == pygame.QUIT:
            running = False
    if any(mouse_buttons):
        # 滑鼠事件
        mouse_pos = pygame.mouse.get_pos()

        # 計算世界座標
        world_x = tool.clamp(0, config.MAP_WIDTH - 1, (mouse_pos[0] + int(config.scroll_x)) // config.BLOCK_SIZE)
        world_y = tool.clamp(0, config.MAP_HEIGHT - 1, (mouse_pos[1] + int(config.scroll_y)) // config.BLOCK_SIZE)
        clicked_block = config.world_data[world_y][world_x]

        if mouse_buttons[0]:
            if clicked_block != "air":
                config.world_data[world_y][world_x] = "air"
        elif mouse_buttons[2]:
            pass

    start_x = max(0, int(config.scroll_x) // config.BLOCK_SIZE)
    end_x = min(config.MAP_WIDTH, (int(config.scroll_x) + config.current_width) // config.BLOCK_SIZE + 1)

    start_y = max(0, int(config.scroll_y) // config.BLOCK_SIZE)
    end_y = min(config.MAP_HEIGHT, (int(config.scroll_y) + config.current_height) // config.BLOCK_SIZE + 1)
    for y_pos in range(start_y, end_y):
        for x_pos in range(start_x, end_x):

            block_name = config.world_data[y_pos][x_pos]
            if block_name == "air":
                continue

            pixel_x = x_pos * config.BLOCK_SIZE - int(config.scroll_x)
            pixel_y = y_pos * config.BLOCK_SIZE - int(config.scroll_y)

            screen.blit(config.img_blocks[block_name], (pixel_x, pixel_y))

    if not player.is_stuck:
        player.handle_input(events)
    player.update(config.world_data)
    player.draw(screen, config.scroll_x, config.scroll_y)

    # 畫面捲動
    target_scroll_x = player.rect.centerx - (config.current_width // 2)
    target_scroll_y = player.rect.centery - (config.current_height // 2)

    # 3. 加上你原本就很厲害的緩動或範圍限制 (利用你寫好的 tool.num_range)
    max_scroll_x = (config.MAP_WIDTH * config.BLOCK_SIZE) - config.current_width
    max_scroll_y = (config.MAP_HEIGHT * config.BLOCK_SIZE) - config.current_height
    config.scroll_x = tool.update_scrolling(config.scroll_x, target_scroll_x, smoth=0.1, max_val=max_scroll_x)
    config.scroll_y = tool.update_scrolling(config.scroll_y, target_scroll_y, smoth=0.1, max_val=max_scroll_y)

    config.scroll_x = tool.clamp(0, max_scroll_x, config.scroll_x)
    config.scroll_y = tool.clamp(0, max_scroll_y, config.scroll_y)

    ui.update(player)
    ui.draw(screen, player)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
