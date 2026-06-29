import os

import pygame

import asset_manager
import config
import tool

# 告訴系統將下一個建立的視窗放在螢幕正中央
os.environ['SDL_VIDEO_CENTERED'] = '1'

pygame.init()
screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT), pygame.RESIZABLE)
running = True
clock = pygame.time.Clock()
screen_text = "2D Minecraft - V0.0.0"

config.img_blocks = asset_manager.load_all_blocks()

while running:
    screen.fill(tool.Colors.BLACK)
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.VIDEORESIZE:
            new_widht = tool.num_range(300, 1400, event.w)
            new_height = tool.num_range(200, 800, event.h)
            screen = pygame.display.set_mode((new_widht, new_height), pygame.RESIZABLE)
        if event.type == pygame.QUIT:
            running = False
    screen.blit(config.img_blocks["grass"], (0, 0))
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
