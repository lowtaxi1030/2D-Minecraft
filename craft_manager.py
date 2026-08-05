from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from player import Player
    from world_manager import World


class Recipe:
    def __init__(self, ingredients: dict[str, int], result_type: str, result_count: int):
        self.ingredients = ingredients  # ex. {"stone": 3, "stick": 2}  # 材料
        self.result = {"type": result_type, "count": result_count}  # ex. {"type": "stone_pickaxe", "count": 1}  # 成品

    def can_craft(self, inventory):
        for item, quantity in self.ingredients.items():
            if inventory.get(item, 0) < quantity:
                return False
        return True

    def craft(self, inventory, player: "Player", world: "World"):  # , item_entity: "ItemEntity"
        if not self.can_craft(inventory):
            return False

        for item, quantity in self.ingredients.items():
            inventory[item] -= quantity
        # player.remove_selected_item(self.ingredients)

        remaining = player.give_item(self.result["type"], self.result["count"])
        if remaining == 0:
            return True

        for _ in range(remaining):
            world.spawn_item_entity(
                {"type": self.result["type"], "count": remaining},
                player.rect.centerx,
                player.rect.top,
                "craft",
                player,
            )
        return False


class CraftingManager:
    def __init__(self):
        pass
