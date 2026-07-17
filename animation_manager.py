class Animation:
    def __init__(
        self,
        name,
        frames,
        speed,
        start_frame=0,
        loop=True,
    ):
        self.name = name

        self.frames = frames

        self.speed = speed

        self.frame = start_frame
        self.timer = 0

    def update(self):
        self.timer += 1

        if self.timer >= self.speed:
            self.timer = 0
            self.frame += 1
            self.frame %= len(self.frames)

    @property
    def image(self):
        return self.frames[self.frame]
