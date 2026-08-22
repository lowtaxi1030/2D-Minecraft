from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from player import Player


class Chest:
    def __init__(self, player: Player):
        self.player = player

    def interact(self):
        self.player.inv_type = "chest"
        print("player is interacting chest")
