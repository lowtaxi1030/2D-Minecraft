# import pygame

import asset_manager as assets
import config
import tool


class MenuManager:
    def __init__(self):
        btn_w, btn_h = 350, 40  # 按鈕標準尺寸
        center_x = config.current_width // 2
        start_y = 150  # 從上方 150 像素開始畫按鈕
        spacing_x = 60  # 左右按鈕的間距
        spacing_y = 50  # 上下按鈕的間距

        self.all_uis = {
            "OPTION": [
                tool.ImageTextButton(
                    name="video_op",
                    image=assets.setting_button_img,
                    text="Video Settings",
                    text_color=tool.Colors.WHITE,
                    pos=(center_x - (btn_w // 2) - spacing_x, start_y + (btn_h // 2)),
                    hover_text_color=tool.Colors.MC_YELLOW,
                ),
                tool.ImageTextButton(
                    name="audio_op",
                    image=assets.setting_button_img,
                    text="Audio Settings",
                    text_color=tool.Colors.WHITE,
                    pos=(center_x + (btn_w // 2) + spacing_x, start_y + (btn_h // 2)),
                    hover_text_color=tool.Colors.MC_YELLOW,
                ),
                tool.ImageTextButton(
                    name="lang_op",
                    image=assets.setting_button_img,
                    text="Lang Settings",
                    text_color=tool.Colors.WHITE,
                    pos=(center_x - (btn_w // 2) - spacing_x, start_y + spacing_y + (btn_h // 2)),
                    hover_text_color=tool.Colors.MC_YELLOW,
                ),
                tool.ImageTextButton(
                    name="done",
                    image=assets.setting_button_img,  # 傳入你的 Minecraft 灰色按鈕圖
                    text="Done",
                    text_color=tool.Colors.WHITE,
                    pos=(center_x, config.current_height - 60),
                    hover_text_color=tool.Colors.MC_YELLOW,
                ),
            ]
        }

    def update(self, events, mouse_pos):
        for ob in self.all_uis["OPTION"]:
            ob.update(events, mouse_pos)

            if ob.name == "done" and ob.is_clicked:
                config.game_state = "PLAYING"

    def draw_options(self, screen):
        # 1. 🎯 鋪滿暗色泥土背景（Minecraft 經典風格）
        for y_pos in range(config.current_height // 40 + 2):
            for x_pos in range(config.current_width // 40 + 2):
                screen.blit(assets.bg_dirt_img, (x_pos * 40, y_pos * 40))
        tool.screen_vague(0)

        # 2. 🎯 畫標題 "Options" (設定)
        tool.show_text(screen, "Options", tool.Colors.WHITE, 0, 50, 40, screen_center=True)

        center_x = config.current_width // 2  # 👈 確保用最新的動態寬度
        start_y = 150
        btn_w, btn_h = 350, 40
        spacing_x = 60
        spacing_y = 50

        # 3. 🎯 用一個簡單的迴圈，自動把所有按鈕的位置更新到最新狀態
        for ob in self.all_uis["OPTION"]:
            if ob.name == "video_op":
                ob.rect.center = (center_x - (btn_w // 2) - spacing_x, start_y + (btn_h // 2))
            elif ob.name == "audio_op":
                ob.rect.center = (center_x + (btn_w // 2) + spacing_x, start_y + (btn_h // 2))
            elif ob.name == "lang_op":
                ob.rect.center = (center_x - (btn_w // 2) - spacing_x, start_y + spacing_y + (btn_h // 2))
            elif ob.name == "done":
                ob.rect.center = (center_x, config.current_height - 60)  # 👈 確保 Done 大按鈕也完美黏在底部

            ob.draw(screen)

    def handle_event(self, event):
        # 🎯 專門負責檢查點擊按鈕的事件
        pass
