from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pygame


import tool
from events.damage_event import DamageEvent
from events.death_event import DeathEvent

from .physical_entity import PhysicalEntity


class LivingEntity(PhysicalEntity):
    def __init__(self, rect: pygame.Rect):
        super().__init__(rect)

        self.gravity = 40  # 格/秒²

        self.max_hp = 20
        self.hp = self.max_hp

        self.dead = False

        self.facing = 1  # 向右

    def heal(self, amount: int):
        self.hp += amount
        self.hp = tool.clamp(0, self.max_hp, self.hp)

    def take_damage(self, damage: int):
        self.pending_events.append(DamageEvent(entity=self, amount=damage))
        self.hp -= damage
        self.hp = tool.clamp(0, self.max_hp, self.hp)

        if self.hp <= 0:
            self.die()

    def die(self):
        self.dead = True

        self.vel_x = 0
        self.vel_y = 0
        self.pending_events.append(DeathEvent(entity=self))
