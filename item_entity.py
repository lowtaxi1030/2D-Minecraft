class ItemEntity:
    def __init__(self, item_type, count, rect, vel_x, vel_y):
        self.item_type = item_type
        self.count = count
        self.rect = rect
        self.vel_x = vel_x
        self.vel_y = vel_y

    def update(self):
        pass

    def draw(self):
        pass
