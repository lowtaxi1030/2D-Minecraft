from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

import tool

from .entity import Entity


class LivingEntity(Entity):
    def __init__(self, rect):
        super().__init__(rect)
        self.gravity = 40

        self.max_hp = 20
        self.hp = self.max_hp

        self.dead = False

        # self.facing = 1  # 向右

    def heal(self, amount: int):
        self.hp += amount
        self.hp = tool.clamp(0, self.max_hp, self.hp)

    def take_damage(self, damage: int):
        self.hp -= damage
        self.hp = tool.clamp(0, self.max_hp, self.hp)

        if self.hp <= 0:
            self.die()

    def die(self):
        self.dead = True
        self.vel_x = 0
        self.vel_y = 0
