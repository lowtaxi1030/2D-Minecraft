from .entity import Entity


class EntityManager:
    def __init__(self):
        self.entities: list[Entity] = []

    def add(self, entity: Entity):
        self.entities.append(entity)

    def remove(self, entity: Entity):
        if entity in self.entities:
            self.entities.remove(entity)

    def update(self, *args, **kwargs):
        for entity in self.entities:
            entity.update(*args, **kwargs)

        self.entities = [entity for entity in self.entities if not entity.remove]

    def draw(self, screen, *args, **kwargs):
        for entity in self.entities:
            entity.draw(screen, *args, **kwargs)
