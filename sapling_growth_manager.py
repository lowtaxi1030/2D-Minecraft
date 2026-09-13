from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from chunk_manager import Chunk
    from tree_generator import TreeGenerator

import random

import config
import tool


class SaplingGrowthManager:
    def __init__(self, chunks, tree_generator: TreeGenerator):
        self.chunks = chunks
        self.tree_generator = tree_generator
        self.TICKS_PER_ATTEMPT = 30
        self.attempts_per_chunk = 10
        self.tick_counter = 0

        self.grow_chance = 0.1

    def update(self):
        self.tick_counter += 1
        if self.tick_counter < self.TICKS_PER_ATTEMPT:
            return
        self.tick_counter = 0

        for chunk_x, chunk in self.chunks.items():
            self._attempt_grow_sapling(chunk_x, chunk)

    def _attempt_grow_sapling(self, chunk_x, chunk: Chunk):
        local_x = random.randint(0, config.CHUNK_WIDTH - 1)
        world_x = chunk_x * config.CHUNK_WIDTH + local_x

        # 從天空中（Y=0）由上往下找第一個非空氣方塊（即地表）
        for y in range(config.MAP_HEIGHT):
            block = self._get_block(world_x, y)
            if block.endswith("_sapling"):
                below = self._get_block(world_x, y + 1)
                if below is None or below not in config.PLANTABLE_BLOCKS:
                    continue
                if random.random() > self.grow_chance:
                    continue
                sapling_type = self._get_tree_type(block)
                tree_blocks = self.tree_generator.generate(sapling_type, world_x, y + 1, random)
                can_grow = True
                for bx, by, _ in tree_blocks:
                    block = self._get_block(bx, by)
                    if not self._can_grow_into(block):
                        can_grow = False
                        break
                if can_grow:
                    for bx, by, block_type in tree_blocks:
                        self._set_block(bx, by, block_type)

                break

    def _get_tree_type(self, sapling_block: str):
        if sapling_block.endswith("_sapling"):
            return sapling_block[:-8]
        return sapling_block

    @staticmethod
    def _can_grow_into(block_name):
        if tool.is_passable(block_name):
            return True

        if block_name == "snow":
            return True
        return False

    def _get_block(self, world_x: int, world_y: int) -> str | None:
        chunk_x = world_x // config.CHUNK_WIDTH
        local_x = world_x % config.CHUNK_WIDTH

        if chunk_x in self.chunks and 0 <= world_y < config.MAP_HEIGHT:
            return self.chunks[chunk_x].blocks[world_y][local_x]
        return None

    def _set_block(self, world_x: int, world_y: int, block_type: str):
        chunk_x = world_x // config.CHUNK_WIDTH
        local_x = world_x % config.CHUNK_WIDTH

        if chunk_x in self.chunks and 0 <= world_y < config.MAP_HEIGHT:
            self.chunks[chunk_x].blocks[world_y][local_x] = block_type
            self.chunks[chunk_x].is_dirty = True
