from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from chunk_manager import ChunkManager
    from fluid_manager import FluidManager


class EventContext:

    def __init__(
        self,
        keys: dict[int, bool],
        chunk_manager: ChunkManager,
        fluid_manager: FluidManager,
    ):
        self.keys = keys
        self.chunk_manager = chunk_manager
        self.fluid_manager = fluid_manager
