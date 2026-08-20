import config
from config import Item
from game_data import furnace_recipes
from game_data.furnace_recipes import FURNACE_FUELS


class FurnaceState:
    """
    1.判斷能不能燒\n
    2.判斷燃料能不能用\n
    3.開始燃燒\n
    4.計算剩餘燃燒時間\n
    5.計算烹煮進度\n
    6.完成後產生物品\n
    7.處理燃料消耗\n
    """

    def __init__(self):
        self.input_item: Item | None = None
        self.fuel_item: Item | None = None
        self.output_item: Item | None = None

        self.cook_progress = 0  # 目前這一件物品燒到哪裡
        self.cook_time = 0  # 這個配方總共需要多久

        self.burn_time_left = 0  # 目前燃料還能燒多久
        self.burn_time = 0  # 剛吃進去的燃料總共能燒多久

    def update(self):
        """┼ ┴ ┬ ┤ ├ ─ │ ┌ ┐ └ ┘
                沒燃料
                   ↓
                [等待]
               ↙       ↘
        有燃料         沒燃料
         ↓               ↓
        [燃燒中] ←──── [等待]
         ↓
        cook_progress++
         ↓
        完成？
         ├─ 否 → 繼續燃燒
         └─ 是 → 產生物品
        """
        # 1. 沒火時，若有原料且可燒，嘗試點燃燃料
        if not self._is_burning():
            if self._has_valid_recipe_and_space():
                self._try_add_fuel()

        # 2. 燃燒邏輯
        if self._is_burning():
            self.burn_time_left -= 1

            recipe = furnace_recipes.get_recipe(self.input_item["type"]) if self.input_item else None

            # 確保有配方且輸出格放得下
            if recipe and self._can_cook_output(recipe):
                self.cook_time = recipe.get("cook_time", 240)
                self.cook_progress += 1

                # 燒鍊完成
                if self.cook_progress >= self.cook_time:
                    self._send_result(recipe)
            else:
                # 沒原料或產物格滿了，進度倒退
                self.cook_progress = max(0, self.cook_progress - 2)
        else:
            # 沒火且沒燃料可點時，進度歸零
            self.cook_progress = 0

    def _can_burn(self):
        if self.fuel_item is None:
            return False
        return self.fuel_item["type"] in FURNACE_FUELS

    def _is_burning(self):
        return self.burn_time_left > 0

    def _has_valid_recipe_and_space(self):
        """檢查是否有原料、配方合法，且輸出格放得下"""
        if self.input_item is None:
            return False

        recipe = furnace_recipes.get_recipe(self.input_item["type"])
        if recipe is None:
            return False

        return self._can_cook_output(recipe)

    def _can_cook_output(self, recipe):
        """檢查輸出格是否相容且未達最大堆疊數"""
        if self.output_item is None:
            return True

        if self.output_item["type"] != recipe["result_type"]:
            return False

        return self.output_item["count"] + recipe.get("result_count", 1) <= config.MAX_STACK

    def _try_add_fuel(self):
        """若燃料格有燃料，消耗 1 個燃料並設定燃燒時間"""
        if not self._can_burn():
            return

        fuel_type = self.fuel_item["type"]
        burn_duration = FURNACE_FUELS[fuel_type]

        self.burn_time = burn_duration
        self.burn_time_left = burn_duration

        # 扣除燃料
        self.fuel_item["count"] -= 1
        if self.fuel_item["count"] <= 0:
            self.fuel_item = None

    def _send_result(self, recipe):
        self.cook_progress = 0

        # 扣除輸入原料
        self.input_item["count"] -= 1
        if self.input_item["count"] <= 0:
            self.input_item = None

        # 增加產出物
        res_type = recipe["result_type"]
        res_count = recipe.get("result_count", 1)

        if self.output_item is None:
            self.output_item = {"type": res_type, "count": res_count}
        else:
            self.output_item["count"] += res_count
