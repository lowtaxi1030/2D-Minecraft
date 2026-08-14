from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from player import Player


class Furnace:
    def __init__(self, player: Player):
        self.player = player
        self.is_burning = False  # 有在燒東西，之後改名

    def interact(self):
        self.player.crafting_type = "furnace"
        # print("player is interacting furnace")
