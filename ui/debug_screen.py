from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from asset_manager import AssetManager
    from camera import Camera
    from chunk_manager import ChunkManager
    from player import Player
    from world_manager import World

import pygame

import config
import tool

from .element import ui_widgets as ui


class DebugScreen:
    def __init__(self, assets: AssetManager):
        # self.assets = assets

        self.debug_frame = 0

        self.left_text = ui.Text(
            name="left_text",
            text="",
            pos=(10, 10),
            colors=tool.Colors.WHITE,
            size=18,
        )

        self.right_text = ui.Text(
            name="left_text",
            text="",
            pos=(config.current_width - 300, 10),
            colors=tool.Colors.WHITE,
            size=18,
        )

    def update(self, player: Player, fps, mouse_pos: tuple[int, int], camera: Camera, world: World, chunk_manager: ChunkManager):
        self.debug_frame += 1

        if self.debug_frame >= 12:
            self.debug_frame = 0

            world_mouse_x, world_mouse_y = camera.screen_to_world(mouse_pos)

            show_mouse_y = 63 + (config.BASE_LINE - world_mouse_y)

            player_block_x = player.hitbox.centerx // config.BLOCK_SIZE
            player_block_y = player.hitbox.centery // config.BLOCK_SIZE

            show_player_y = 63 + (config.BASE_LINE - player_block_y)

            current_chunk = player.hitbox.centerx // (config.CHUNK_WIDTH * config.BLOCK_SIZE)
            local_x = player_block_x % config.CHUNK_WIDTH

            standing_block = (
                "None"
                if player.is_flying
                else chunk_manager.get_block(
                    player.hitbox.centerx,
                    tool.clamp(
                        0,
                        config.MAP_HEIGHT * config.BLOCK_SIZE - 1,
                        player.hitbox.bottom,
                    ),
                ).replace("_", " ")
            )

            raw_mouse_block = chunk_manager.get_block(
                world_mouse_x * config.BLOCK_SIZE,
                world_mouse_y * config.BLOCK_SIZE,
            )
            mouse_block = world.get_block_base_name(raw_mouse_block).replace("_", " ")

            # top_y = tool.clamp(0, config.MAP_HEIGHT - 1, int(player.hitbox.top // config.BLOCK_SIZE))

            self.left_text.text = [
                "=== Player ===",
                f"Pos : ({player_block_x}, {show_player_y})",  # show_player_y
                f"Vel : ({player.vel_x:.2f}, {player.vel_y:.2f})",
                f"Grounded : {player.is_grounded}",
                f"Flying : {player.is_flying}",
                f"Mode : {player.mode}",
                f"Facing : {'Right' if player.facing == 1 else 'Left'}",
                f"Is Submerged: {player.is_submerged}",
                f"Is Swmming: {player.is_swimming}",
                "",
                "=== Block ===",
                f"Mouse Pos : ({world_mouse_x}, {show_mouse_y})",  # show_mouse_y
                f"Mouse : {mouse_block}",
                f"Standing : {standing_block}",
                "",
                "=== Performance ===",
                f"FPS : {fps:.0f}",
                f"Screen Mouse Pos: {mouse_pos}",
                f"Player Screen Pos: ({player.hitbox.centerx - camera.scroll_x:.0f}, {player.hitbox.centery - camera.scroll_y:.0f})",
                f"Loaded Chunks : {len(chunk_manager.chunks)}",
                f"Entities : {len(world.item_entities)}",
                f"Dirty Chunks : {sum(chunk.is_dirty for chunk in chunk_manager.chunks.values())}",
            ]

            self.right_text.text = [
                "=== World ===",
                f"World : {config.CURRENT_WORLD}",
                f"Seed : {config.WORLD_SEED}",
                f"Chunk : {current_chunk}",
                f"Local X : {local_x}",
                f"Biome : {chunk_manager.get_biome(player.hitbox.centerx // config.BLOCK_SIZE)}",
                "",
                "=== Camera ===",
                f"Scroll : ({camera.scroll_x:.1f}, {camera.scroll_y:.1f})",
                f"Zoom : {camera.zoom:.2f}",
                "",
            ]

    def draw(self, screen: pygame.Surface):
        self.left_text.draw(screen)
        self.right_text.draw(screen)
