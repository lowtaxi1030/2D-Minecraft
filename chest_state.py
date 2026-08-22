import config


class ChestState:
    def __init__(self):
        self.grids: list[config.Item | None] = [None] * 27
        self.width = 9
        self.height = 3
    def to_dict(self):
        return {"grids": self.grids, "width": self.width, "height": self.height}

    @classmethod
    def from_dict(cls, data):
        state = cls()
        state.grids = data.get("grids", [None] * 27)
        state.width = data.get("width", 9)
        state.height = data.get("height", 3)
        return state
