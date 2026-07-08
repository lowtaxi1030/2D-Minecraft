import os

import pygame

import asset_manager as assets
import camera
import config
import menu_manager
import tool
import ui_manager
import world_generator
from player import Player

# 告訴系統將下一個建立的視窗放在螢幕正中央
os.environ['SDL_VIDEO_CENTERED'] = '1'

game_camera = camera.Camera()

pygame.init()
screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT), pygame.RESIZABLE)
world_surface = pygame.Surface((config.current_width, config.current_height))
clock = pygame.time.Clock()
# screen_text = "2D Minecraft - V0.0.0"
pygame.display.set_caption("2D Minecraft - V0.0.0")  # 之後放screen_text

assets.load_all_blocks()
# config.org_img_blocks = config.img_blocks.copy()

config.world_data = world_generator.make_map(config.MAP_WIDTH, config.MAP_HEIGHT)
player = Player(100, 0)

ui = ui_manager.UI()
menu = menu_manager.MenuManager()

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

        world_x, world_y = game_camera.screen_to_world(mouse_pos)
        if any(mouse_buttons):
            # 計算世界座標
            if not (world_x < 0 or world_x > config.MAP_WIDTH or world_y < 0 or world_y > config.MAP_HEIGHT):
                clicked_block = config.world_data[world_y][world_x]

                if mouse_buttons[0]:
                    if clicked_block != "air":
                        config.world_data[world_y][world_x] = "air"

                # 放置方塊
                elif mouse_buttons[2] and clicked_block == "air":
                    current_item = player.hotbar[player.selected_hotbar_index]

                    if current_item is not None:
                        new_block_rect = pygame.Rect(
                            world_x * int(config.BLOCK_SIZE),
                            world_y * int(config.BLOCK_SIZE),
                            int(config.BLOCK_SIZE),
                            int(config.BLOCK_SIZE),
                        )
                        if not player.rect.colliderect(new_block_rect):
                            # 成功放置！
                            config.world_data[world_y][world_x] = current_item["type"]

        game_camera.draw_world(world_surface, mouse_pos)

        if not player.is_stuck:
            player.handle_input(events)
        player.update(config.world_data)
        player.draw(world_surface, game_camera.scroll_x, game_camera.scroll_y)

        game_camera.update(player)
        game_camera.draw(screen, world_surface)

        ui.update(player)
        ui.draw(screen, player, config.show_debug_screen)

    elif config.game_state == "PAUSE":
        player.draw(screen, game_camera.scroll_x, game_camera.scroll_y)
        game_camera.draw_world(screen, mouse_pos, draw_hover=False)

        menu.update(events, mouse_pos)
        menu.draw(screen)

    elif config.game_state == "OPTION":
        player.draw(screen, game_camera.scroll_x, game_camera.scroll_y)
        game_camera.draw_world(screen, mouse_pos, draw_hover=False)

        menu.update(events, mouse_pos)
        menu.draw(screen)

    elif config.game_state == "VIDEO_OPTION":
        player.draw(screen, game_camera.scroll_x, game_camera.scroll_y)
        game_camera.draw_world(screen, mouse_pos, draw_hover=False)

        menu.update(events, mouse_pos)
        menu.draw(screen)
        game_camera.zoom = config.ORG_FOV / config.fov

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
