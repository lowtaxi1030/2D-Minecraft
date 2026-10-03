from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    import pygame

    from contextes.update_context import UpdateContext

from .entity import Entity

T = TypeVar("T", bound=Entity)


class EntityManager:
    def __init__(self):
        self.entities: list[Entity] = []

    def add(self, entity: Entity):
        self.entities.append(entity)

    def remove(self, entity: Entity):
        if entity in self.entities:
            self.entities.remove(entity)

    def handle_input(self):
        for entity in self.entities:
            entity.handle_input()

    def handle_event(self, event, context):
        for entity in self.entities:
            entity.handle_event(event, context)

    def update(self, context: UpdateContext, dt):
        for entity in self.entities:
            entity.update(context, dt)

        self.entities = [entity for entity in self.entities if not entity.remove]

    def draw(self, screen, *args, **kwargs):
        for entity in self.entities:
            entity.draw(screen, *args, **kwargs)

    """實用工具"""

    def get_entities_in_rect(self, rect: pygame.Rect):
        for entity in self.entities:
            if entity.rect.colliderect(rect):
                yield entity

    def get_entities_by_type(
        self,
        entity_type: type[T],
    ) -> Iterator[T]:
        for entity in self.entities:
            if isinstance(entity, entity_type):
                yield entity
