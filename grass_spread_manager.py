import random

import config


class GrassSpreadManager:
    def __init__(self, chunks):
        self.chunks = chunks
        self.TICKS_PER_ATTEMPT = 20  # 每嘗試一次，間隔幾個tick
        self.tick_counter = 0  # 新增：記錄目前累積了幾個tick
        self.attempts_per_chunk = 5  # 每次抽幾顆

    def update(self):
        self.tick_counter += 1
        if self.tick_counter < self.TICKS_PER_ATTEMPT:
            return
        self.tick_counter = 0

        for chunk_x, chunk in self.chunks.items():
            self._try_spread_in_chunk(chunk_x, chunk)

    def _try_spread_in_chunk(self, chunk_x, chunk):
        for _ in range(self.attempts_per_chunk):
            local_x = random.randint(0, config.CHUNK_WIDTH - 1)
            y = random.randint(0, config.MAP_HEIGHT - 1)
            world_x = chunk_x * config.CHUNK_WIDTH + local_x

            self._try_spread_at(world_x, y)

    def _try_spread_at(self, world_x, world_y):
        # local_x = world_x % config.CHUNK_WIDTH

        block = self._get_block(world_x, world_y)
        if block != "dirt":
            return

        top = self._get_block(world_x, world_y - 1)
        if top is not None and top == "air":
            self._set_block(world_x, world_y, "grass")

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
