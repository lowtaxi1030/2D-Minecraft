import os

import pygame

import asset_manager as assets
import camera

# import chunk_manager
import config
import menu_manager
import save_manager
import tool
import ui_manager

# import world_generator
import world_manager
from player import Player

save = save_manager.SaveManager()

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

player = Player(0, 20)
ui = ui_manager.UI()
menu = menu_manager.MenuManager()
world = world_manager.World()

last_chunk = None

save.load_world(player)

while config.running:
    events = pygame.event.get()
    keys = pygame.key.get_pressed()
    mouse_buttons = pygame.mouse.get_pressed()
    mouse_pos = pygame.mouse.get_pos()
    screen.fill(tool.Colors.CYAN)

    fps = clock.get_fps()

    if config.game_state == "MENU":
        pass

    elif config.game_state == "PLAYING":
        current_chunk = player.rect.centerx // (config.CHUNK_WIDTH * config.BLOCK_SIZE)

        surface_width = int(config.current_width / game_camera.zoom)
        surface_height = int(config.current_height / game_camera.zoom)

        world_surface = pygame.Surface((surface_width, surface_height))
        world_surface.fill(tool.Colors.CYAN)

        game_camera.draw_world(world_surface, mouse_pos)

        dropped_item = None

        player.handle_input(mouse_pos)

        for event in events:
            item = player.handle_event(event, keys)

            if item is not None:
                dropped_item = item

            ui.handle_events(event, player, mouse_pos)

        # 更新
        world.update(mouse_buttons, mouse_pos, player, game_camera)
        player.update()
        game_camera.update(player)
        ui.update(player, fps, mouse_pos, game_camera)

        if dropped_item is not None:
            world.spawn_item_entity(dropped_item, player.rect.centerx, player.rect.top, "drop", player)

        # print(player.rect.x, player.rect.y)
        # print(game_camera.scroll_x, game_camera.scroll_y)

        # 畫圖
        player.draw(world_surface, game_camera.scroll_x, game_camera.scroll_y)
        world.draw(world_surface, game_camera.scroll_x, game_camera.scroll_y, game_camera.zoom)
        game_camera.draw(screen, world_surface)
        ui.draw(screen, player, fps, mouse_pos, game_camera)

        if current_chunk != last_chunk:
            game_camera._load_visible_chunks(player)
            last_chunk = current_chunk

    elif config.game_state == "PAUSE":
        screen.blit(config.pause_background, (0, 0))

        menu.update(events, mouse_pos)
        menu.draw(screen)

    elif config.game_state == "OPTION":
        screen.blit(config.pause_background, (0, 0))

        menu.update(events, mouse_pos)
        menu.draw(screen)

    elif config.game_state == "VIDEO_OPTION":
        screen.blit(config.pause_background, (0, 0))

        menu.update(events, mouse_pos)
        menu.draw(screen)
        game_camera.zoom = config.ORG_FOV / config.fov

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
                    config.pause_background = screen.copy()
                    config.game_state = "PAUSE"
                if event.key == pygame.K_F3:
                    config.show_debug_screen = not config.show_debug_screen

    pygame.display.flip()
    clock.tick(60)

pygame.quit()

save.save_world(player)
