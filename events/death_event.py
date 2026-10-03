from dataclasses import dataclass

from entity.entity import Entity


@dataclass
class DeathEvent:
    entity: Entity
