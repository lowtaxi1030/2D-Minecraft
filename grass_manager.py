import random

import config


class GrassManager:
    def __init__(self, chunks):
        self.grass_spread_manager = GrassSpreadManager(chunks)
        self.grass = GrassDecayManager(chunks)

    def update(self):
        self.grass_spread_manager.update()
        self.grass.update()


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


class GrassDecayManager:
    def __init__(self, chunks):
        self.chunks = chunks
        self.TICKS_PER_CHECK = 20
        self.tick_counter = 0

    def update(self):
        self.tick_counter += 1
        if self.tick_counter < self.TICKS_PER_CHECK:
            return
        self.tick_counter = 0

        for chunk_x, chunk in self.chunks.items():
            self._check_decay(chunk_x, chunk)

    def _check_decay(self, chunk_x, chunk):
        for local_x in range(config.CHUNK_WIDTH):
            world_x = chunk_x * config.CHUNK_WIDTH + local_x
            for world_y in range(config.MAP_HEIGHT):
                if self._should_decay(world_x, world_y):
                    self._set_block(world_x, world_y, "dirt")

    def _should_decay(self, world_x: int, world_y: int) -> bool:
        self_block = self._get_block(world_x, world_y)
        if self_block != "grass":
            return False

        top_block = self._get_block(world_x, world_y - 1)

        if top_block is None or top_block == "air":
            return False
        # 檢查是否為液體
        is_fluid = any(top_block.endswith(fluid) for fluid in config.TYPES_OF_FLUID)

        # 只要不是空氣，且是實體方塊或液體，就觸發退化
        if is_fluid or top_block != "air":
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
