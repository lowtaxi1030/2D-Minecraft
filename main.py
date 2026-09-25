import os
import time

import opensimplex
import pygame

import asset_manager
import camera
import config
import save_manager
import tool
import world_manager
from chunk_manager import ChunkManager
from craft_manager import CraftingManager
from environment_systems import EnvironmentSystems
from fluid_manager import FluidManager
from game_data import crafting_recipes
from player import Player
from ui import ui_manager

chunk_manager = ChunkManager()

save = save_manager.SaveManager(chunk_manager)
crafting_manager = CraftingManager()

# 告訴系統將下一個建立的視窗放在螢幕正中央
os.environ["SDL_VIDEO_CENTERED"] = "1"

pygame.init()
screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT), pygame.RESIZABLE)
world_surface = pygame.Surface((config.current_width, config.current_height))
clock = pygame.time.Clock()
# screen_text = f"2D Minecraft - {config.GAME_VERSION}"
pygame.display.set_caption(f"2D Minecraft - {config.GAME_VERSION}")  # 之後放screen_text


player = Player(0, 80, chunk_manager)

asset = asset_manager.AssetManager()
asset.load()

ui = ui_manager.UI(asset)
world = world_manager.World(asset, chunk_manager)

last_chunk = None

save.load_world(player, world)

game_camera = camera.Camera(asset, player, chunk_manager)
environment_systems = EnvironmentSystems(chunk_manager.chunks)
fluid_manager = FluidManager(chunk_manager.chunks)

crafting_recipes.register_recipes(crafting_manager)
# print("Recipes registered:", len(crafting_manager.recipes))
# print("Registered recipes:")
# for recipe in crafting_manager.recipes:
#     print(f"Ingredients: {recipe.ingredients}, Result: {recipe.result['type']} x{recipe.result['count']}")


frame_timers = {}
frame_count = 0

dt = 0
opensimplex.noise2(0, 0)  # 逼 numba 先暖機

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
        current_chunk = player.hitbox.centerx // (config.CHUNK_WIDTH * config.BLOCK_SIZE)
        game_camera.update(player, fluid_manager, dt)

        surface_width = int(config.current_width / game_camera.zoom)
        surface_height = int(config.current_height / game_camera.zoom)

        world_surface = pygame.Surface((surface_width, surface_height))
        world_surface.fill(tool.Colors.CYAN)

        t0 = time.perf_counter()
        game_camera.draw_world(world_surface, mouse_pos, world)
        frame_timers["camera.draw_world"] = frame_timers.get("camera.draw_world", 0) + (time.perf_counter() - t0)

        dropped_item = None

        player.handle_input()
        ui.handle_input()

        t1 = time.perf_counter()
        player.just_switched_mode = False
        for event in events:
            item = player.handle_event(event, keys, fluid_manager)

            if item is not None:
                dropped_item = item

            ui.handle_events(event, player, mouse_pos, world, crafting_manager)
        frame_timers["event_loop"] = frame_timers.get("event_loop", 0) + (time.perf_counter() - t1)

        # 更新
        """任何一幀裡，只要牽涉到「滑鼠螢幕座標 → 世界座標」的換算，都必須使用「跟這一幀實際顯示畫面一致」的那個 zoom 值"""
        t2 = time.perf_counter()
        # t2_1 = time.perf_counter()
        player.update(mouse_pos, dt, game_camera, fluid_manager)
        frame_timers["player.update"] = frame_timers.get("player.update", 0) + (time.perf_counter() - t2)

        t3 = time.perf_counter()
        world.update(mouse_buttons, mouse_pos, player, game_camera, fluid_manager, environment_systems, ui)
        frame_timers["world.update"] = frame_timers.get("world.update", 0) + (time.perf_counter() - t3)

        t4 = time.perf_counter()
        ui.update(events, player, fps, mouse_pos, mouse_buttons, game_camera, world, chunk_manager)
        frame_timers["ui.update"] = frame_timers.get("ui.update", 0) + (time.perf_counter() - t4)

        t5 = time.perf_counter()
        asset.update()
        fluid_manager.update(pygame.time.get_ticks())
        frame_timers["asset_fluid_update"] = frame_timers.get("asset_fluid_update", 0) + (time.perf_counter() - t5)

        # frame_timers["all_updates"] = frame_timers.get("all_updates", 0) + (time.perf_counter() - t2_1)

        if dropped_item is not None:
            world.spawn_item_entity(dropped_item, player.hitbox.centerx, player.hitbox.top, "drop", player)

        for item in player.pending_drops:
            world.spawn_item_entity(item, player.hitbox.centerx, player.hitbox.top, "death", player)
        player.pending_drops.clear()

        # print(player.rect.x, player.rect.y)
        # print(game_camera.scroll_x, game_camera.scroll_y)

        # t3_1 = time.perf_counter()
        # 畫圖
        t6 = time.perf_counter()
        player.draw(world_surface, game_camera.scroll_x, game_camera.scroll_y)
        world.draw(world_surface, game_camera.scroll_x, game_camera.scroll_y, game_camera.zoom)
        frame_timers["draw_to_surface"] = frame_timers.get("draw_to_surface", 0) + (time.perf_counter() - t6)

        t7 = time.perf_counter()
        game_camera.draw(screen, world_surface)
        frame_timers["camera.draw(smoothscale)"] = frame_timers.get("camera.draw(smoothscale)", 0) + (time.perf_counter() - t7)

        t8 = time.perf_counter()
        ui.draw(screen, player)
        frame_timers["ui.draw"] = frame_timers.get("ui.draw", 0) + (time.perf_counter() - t8)

        # frame_timers["all_draws"] = frame_timers.get("all_draws", 0) + (time.perf_counter() - t3_1)

        # 不要顯示ui
        if player.is_die:
            config.pause_background = screen.copy()
            config.game_state = "DEATH"

        ui.draw(screen, player)

        if current_chunk != last_chunk:
            t9 = time.perf_counter()
            game_camera._load_visible_chunks(player, fluid_manager)
            chunk_load_time = time.perf_counter() - t9
            print(f"[chunk載入] 花了 {chunk_load_time*1000:.2f}ms")  # 獨立即時印出，不進平均
            last_chunk = current_chunk

    elif config.game_state in ui.menu_manager.menus:
        if config.pause_background is not None:
            screen.blit(config.pause_background, (0, 0))
        else:
            screen.fill(tool.Colors.CYAN)  # 或者用一個預設背景顏色
        ui.update(events, player, fps, mouse_pos, mouse_buttons, game_camera, world, chunk_manager)
        ui.draw(screen, player)

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

    t10 = time.perf_counter()
    pygame.display.flip()
    frame_timers["flip"] = frame_timers.get("flip", 0) + (time.perf_counter() - t10)
    dt = clock.tick(60) / 1000.0

    frame_count += 1
    if frame_count >= 60 and config.fps_check:
        total = sum(frame_timers.values())
        breakdown = " | ".join(f"{k}: {v/frame_count*1000:.2f}ms" for k, v in frame_timers.items())
        print(f"[FPS:{clock.get_fps():.0f}] 平均每幀: {total/frame_count*1000:.2f}ms | {breakdown}")
        frame_timers = {}
        frame_count = 0

pygame.quit()

save.save_world(player, world)
