from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from config import Item


class SlotHandler:
    def handle_slot_left_click(self, held_item: Item, target_item: Item):
        """
        | 手上 | 目標格 | 動作   |\n
        ——————————————————————————\n
        | 空   | 空     | 不做事 |\n
        | 空   | 有     | 拿起   |\n
        | 有   | 空     | 放下   |\n
        | 有   | 同種   | 合併   |\n
        | 有   | 不同種 | 交換   |\n
        """
        # 處理「拿、放、合併、交換」
        if held_item is None:
            if target_item is None:
                return held_item, target_item
            held_item = target_item.copy()
            target_item = None

        elif target_item is None:
            target_item = held_item.copy()
            held_item = None

        elif held_item["type"] == target_item["type"]:
            target_item, held_item = self._try_merge_stack(target_item, held_item)

        else:
            target_item, held_item = held_item.copy(), target_item.copy()

        return held_item, target_item

    def handle_slot_right_click(self, held_item: Item, target_item: Item):
        if held_item is None:
            if target_item is None:
                return held_item, target_item

            held_count = (target_item["count"] + 1) // 2

            held_item = {
                "type": target_item["type"],
                "count": held_count,
            }

            target_item["count"] -= held_count

            if target_item["count"] == 0:
                target_item = None
        elif target_item is None:
            held_item["count"] -= 1

            target_item = {"type": held_item["type"], "count": 1}

            # _set_slot(player, area, index, {"type": held_item["type"], "count": 1})

            if held_item["count"] == 0:
                held_item = None

        elif target_item["type"] == held_item["type"]:
            if target_item["count"] < 64:
                held_item["count"] -= 1

                target_item["count"] += 1

            if held_item["count"] == 0:
                held_item = None

        return held_item, target_item

    def handle_output_slot_click(self, held_item: Item, result_item: Item):
        # 只允許拿取，不允許放入

        # 1.如果成品格是空的
        if result_item is None:
            pass

        # 2.如果手上沒東西
        elif held_item is None:
            held_item, result_item = result_item.copy(), None

        # 3.如果手上已經有東西
        else:
            if held_item["type"] == result_item["type"]:
                held_item, result_item = self._try_merge_stack(held_item, result_item)

        return held_item, result_item

    def _try_merge_stack(self, dst_item: Item, src_item: Item):
        """
        dst_item: 目標格
        src_item: 來源(通常是滑鼠)
        """

        if dst_item["type"] != src_item["type"]:
            return dst_item, src_item

        total = dst_item["count"] + src_item["count"]

        if total <= 64:
            dst_item["count"] = total
            src_item = None
        else:
            src_item["count"] = total - 64
            dst_item["count"] = 64

        return dst_item, src_item
