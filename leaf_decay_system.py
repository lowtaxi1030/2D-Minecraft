import random

import config


class LeafDecaySystem:
    def __init__(self, chunks):
        self.chunks = chunks
        self.TICKS_PER_ATTEMPT = 10
        self.attempts_per_chunk = 20
        self.tick_counter = 0
        self.LOG_CHECK_RADIUS = 4  # 附近多近有原木就不衰變
        self.DECAY_CHANCE = 0.7

    def update(self):
        self.tick_counter += 1
        if self.tick_counter < self.TICKS_PER_ATTEMPT:
            return []
        self.tick_counter = 0

        decayed = []
        for chunk_x, chunk in self.chunks.items():
            decayed.extend(self._try_decay_in_chunk(chunk_x, chunk))
        return decayed

    def _try_decay_in_chunk(self, chunk_x, chunk) -> list[tuple[int, int, int]]:
        results = []
        for _ in range(self.attempts_per_chunk):
            local_x = random.randint(0, config.CHUNK_WIDTH - 1)
            y = random.randint(0, config.MAP_HEIGHT - 1)
            world_x = chunk_x * config.CHUNK_WIDTH + local_x

            if (result := self._try_decay_at(world_x, y)) is not None:
                results.append(result)
        return results

    def _try_decay_at(self, world_x, world_y) -> (tuple[int, int, int] | None):
        if (block := self._get_block(world_x, world_y)) is None:
            return

        if not self.is_natural_leaf(block):
            return

        if self._has_nearby_log(world_x, world_y):
            return

        if random.random() > self.DECAY_CHANCE:
            return

        self._set_block(world_x, world_y, "air")
        return (world_x, world_y, block)

    def _has_nearby_log(self, world_x, world_y):
        for dx in range(-self.LOG_CHECK_RADIUS, self.LOG_CHECK_RADIUS + 1):
            for dy in range(-self.LOG_CHECK_RADIUS, self.LOG_CHECK_RADIUS + 1):
                nx, ny = world_x + dx, world_y + dy
                if (block := self._get_block(nx, ny)) is not None and block.endswith("_log"):
                    return True
        return False

    def is_natural_leaf(self, block_type: str):
        if "leav" not in block_type:
            return False
        if block_type.endswith("_natural"):
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
