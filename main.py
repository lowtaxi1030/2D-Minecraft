import os

import pygame

import asset_manager as assets
import camera
import config
import menu_manager
import tool
import ui_manager
import world_generator
import world_manager
from player import Player

# 告訴系統將下一個建立的視窗放在螢幕正中央
os.environ["SDL_VIDEO_CENTERED"] = "1"

game_camera = camera.Camera()

pygame.init()
screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT), pygame.RESIZABLE)
world_surface = pygame.Surface((config.current_width, config.current_height))
clock = pygame.time.Clock()
# screen_text = "2D Minecraft - V0.0.0"
pygame.display.set_caption("2D Minecraft - V0.0.0")  # 之後放screen_text

assets.load_all_blocks()

config.world_data = world_generator.make_map(config.MAP_WIDTH, config.MAP_HEIGHT)
player = Player(100, 0)

ui = ui_manager.UI()
menu = menu_manager.MenuManager()
world = world_manager.World()

while config.running:
    events = pygame.event.get()
    keys = pygame.key.get_pressed()
    mouse_buttons = pygame.mouse.get_pressed()
    mouse_pos = pygame.mouse.get_pos()
    screen.fill(tool.Colors.CYAN)

    for event in events:
        if event.type == pygame.VIDEORESIZE:
            config.current_width = event.w
            config.current_height = event.h
            screen = pygame.display.set_mode((event.w, event.h), screen.get_flags())

        if event.type == pygame.QUIT:
            config.running = False

        if event.type == pygame.KEYDOWN:
            if config.game_state == "PLAYING":
                if event.key == pygame.K_ESCAPE:
                    config.game_state = "PAUSE"
                if event.key == pygame.K_F3:
                    config.show_debug_screen = not config.show_debug_screen

    if config.game_state == "MENU":
        pass

    elif config.game_state == "PLAYING":
        surface_width = int(config.current_width / game_camera.zoom)
        surface_height = int(config.current_height / game_camera.zoom)

        world_surface = pygame.Surface((surface_width, surface_height))
        world_surface.fill(tool.Colors.CYAN)

        game_camera.draw_world(world_surface, mouse_pos)

        if not player.is_stuck:
            player.handle_input(events)

        # 更新
        world.update(mouse_buttons, mouse_pos, player, game_camera, config.world_data)
        dropped_item = player.update(config.world_data)
        game_camera.update(player)
        ui.update(player)

        if dropped_item is not None:
            world.spawn_item_entity(...)

        # print(player.rect.x, player.rect.y)
        # print(game_camera.scroll_x, game_camera.scroll_y)

        # 畫圖
        player.draw(world_surface, game_camera.scroll_x, game_camera.scroll_y)
        world.draw(world_surface, game_camera.scroll_x, game_camera.scroll_y, game_camera.zoom)
        game_camera.draw(screen, world_surface)
        ui.draw(screen, player)

    elif config.game_state == "PAUSE":
        game_camera.draw_option_bg(player, mouse_pos, screen, world_surface)

        menu.update(events, mouse_pos)
        menu.draw(screen)

    elif config.game_state == "OPTION":
        game_camera.draw_option_bg(player, mouse_pos, screen, world_surface)

        menu.update(events, mouse_pos)
        menu.draw(screen)

    elif config.game_state == "VIDEO_OPTION":
        game_camera.draw_option_bg(player, mouse_pos, screen, world_surface)

        menu.update(events, mouse_pos)
        menu.draw(screen)
        game_camera.zoom = config.ORG_FOV / config.fov

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
