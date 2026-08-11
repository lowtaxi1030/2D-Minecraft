from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from player import Player


class CraftingTable:
    def __init__(self, player: Player):
        self.player = player

    def interact(self):
        self.player.crafting_type = "crafting_table"
        print("player is interacting crafting_table")
