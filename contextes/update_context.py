from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from camera import Camera
    from chunk_manager import ChunkManager
    from entity.player import Player
    from environment_systems import EnvironmentSystems
    from fluid_manager import FluidManager


class UpdateContext:

    def __init__(
        self,
        chunk_manager: ChunkManager,
        fluid_manager: FluidManager,
        environment_systems: EnvironmentSystems,
        game_camera: Camera,
        player: Player,
        mouse_pos: tuple[int, int],
    ):
        self.chunk_manager = chunk_manager
        self.fluid_manager = fluid_manager
        self.environment_systems = environment_systems
        self.game_camera = game_camera
        self.player = player
        self.mouse_pos = mouse_pos
