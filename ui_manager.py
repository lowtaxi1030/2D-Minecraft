import pygame

import asset_manager as assets
import config

pygame.init()


class UI:
    def __init__(self):
        self.all_ui = []
        total_hotbar_width = 9 * (config.SLOT_SIZE + config.PADDING) - config.PADDING

        self.start_x = (config.current_width - total_hotbar_width) // 2
        self.start_y = config.current_height - config.SLOT_SIZE - 10

        self.SLOT_SPACING = 64
        self.block_start_x = assets.select_frame_rect.centerx
        self.block_start_y = assets.select_frame_rect.centery

    def update(self, player):
        
        assets.update_img_pos(assets.hotbar_bg_rect, screen_center=True, is_bottom=True)
        
        assets.select_frame_rect.left = assets.hotbar_bg_rect.left - 1 + (player.selected_hotbar_index * self.SLOT_SPACING)
        assets.select_frame_rect.top = assets.hotbar_bg_rect.top - 3

    def draw(self, screen: pygame.Surface, player):
        screen.blit(assets.hotbar_bg, assets.hotbar_bg_rect)
        screen.blit(assets.select_frame, assets.select_frame_rect)

        self.block_start_x = assets.select_frame_rect.centerx
        self.block_start_y = assets.select_frame_rect.centery

        first_slot_center_x = assets.hotbar_bg_rect.left + 36

        for i in range(9):
            item = player.hotbar[i]
            if item is not None:
                item_center_x = first_slot_center_x + (i * self.SLOT_SPACING)
                item_center_y = assets.select_frame_rect.centery

                block_img = config.img_blocks[item["type"]]

                block_rect = block_img.get_rect()
                block_rect.center = (item_center_x, item_center_y)

                screen.blit(block_img, block_rect)
