import pygame

import asset_manager as assets
import config
import tool
import ui_obs as ui


class MenuManager:
    def __init__(self):
        self.pause_menu = PauseMenu()
        self.option_menu = OptionMenu()
        self.video_menu = VideoMenu()

    def update(self, events, mouse_pos):
        if config.game_state == "PAUSE":
            self.pause_menu.update(events, mouse_pos)
        elif config.game_state == "OPTION":
            self.option_menu.update(events, mouse_pos)
        elif config.game_state == "VIDEO_OPTION":
            self.video_menu.update(events, mouse_pos)

    def draw(self, screen):
        # 1. 🎯 鋪滿暗色泥土背景（Minecraft 經典風格）
        # for y_pos in range(config.current_height // 40 + 2):
        #     for x_pos in range(config.current_width // 40 + 2):
        #         screen.blit(assets.bg_dirt_img, (x_pos * 40, y_pos * 40))

        tool.screen_vague(20)

        if config.game_state == "PAUSE":
            self.pause_menu.draw(screen)
        if config.game_state == "OPTION":
            self.option_menu.draw(screen)
        elif config.game_state == "VIDEO_OPTION":
            self.video_menu.draw(screen)


class BaseMenu:
    """
    之後Menu的class太多時再用，不然要一直修改
    """
    def __init__(self):
        self.btn_w, self.btn_h = 350, 40  # 按鈕標準尺寸
        self.center_x = config.current_width // 2
        self.start_y = 50  # 從上方 150 像素開始畫按鈕
        self.spacing_x = 60  # 左右按鈕的間距
        self.spacing_y = 120  # 上下按鈕的間距

    def update_buttons(self, events, mouse_pos):
        for ob in self.all_uis:
            ob.update(events, mouse_pos)

    def draw_buttons(self, screen):
        for ob in self.all_uis:
            ob.draw(screen)


class PauseMenu:
    def __init__(self):
        self.btn_w, self.btn_h = 350, 40  # 按鈕標準尺寸
        self.center_x = config.current_width // 2
        self.start_y = 50  # 從上方 150 像素開始畫按鈕
        self.spacing_x = 60  # 左右按鈕的間距
        self.spacing_y = 120  # 上下按鈕的間距

        self.back_btn = ui.ImageTextButton(
            name="back_to_game",
            image=assets.setting_button_img,
            pos=(self.center_x, self.start_y + self.spacing_y),
            text="Back to Game",
            text_color=tool.Colors.WHITE,
            hover_text_color=tool.Colors.MC_YELLOW,
        )

        self.option_btn = ui.ImageTextButton(
            name="options",
            image=assets.setting_button_img,
            pos=(self.center_x, self.start_y + self.spacing_y * 2),
            text="Options...",
            text_color=tool.Colors.WHITE,
            hover_text_color=tool.Colors.MC_YELLOW,
        )

        self.quit_btn = ui.ImageTextButton(
            name="save_and_quit",
            image=assets.setting_button_img,
            pos=(self.center_x, self.start_y + self.spacing_y * 3),
            text="Save and Quit",
            text_color=tool.Colors.WHITE,
            hover_text_color=tool.Colors.MC_YELLOW,
        )

        self.all_uis = [self.back_btn, self.option_btn, self.quit_btn]

    def layout(self):
        self.back_btn.rect.center = (self.center_x, self.start_y + self.spacing_y)
        self.option_btn.rect.center = (self.center_x, self.start_y + self.spacing_y * 2)
        self.quit_btn.rect.center = (self.center_x, self.start_y + self.spacing_y * 3)

    def update(self, events, mouse_pos):
        self.center_x = config.current_width // 2

        for ob in self.all_uis:
            ob.update(events, mouse_pos)

        if self.back_btn.is_clicked:
            config.game_state = "PLAYING"

        if self.option_btn.is_clicked:
            config.game_state = "OPTION"

        if self.quit_btn.is_clicked:
            config.running = False

        self._handle_event(events, mouse_pos)
        self.layout()

    def _handle_event(self, events, mouse_pos):
        pass

    def draw(self, screen):
        ui.show_text(screen, "Game Menu", tool.Colors.WHITE, 0, 50, 40, screen_center=True)

        for ob in self.all_uis:
            ob.draw(screen)


class OptionMenu:
    def __init__(self):
        self.btn_w, self.btn_h = 350, 40  # 按鈕標準尺寸
        self.center_x = config.current_width // 2
        self.start_y = 150  # 從上方 150 像素開始畫按鈕
        self.spacing_x = 60  # 左右按鈕的間距
        self.spacing_y = 60  # 上下按鈕的間距

        self.video_button = ui.ImageTextButton(
            name="video_option",
            image=assets.setting_button_img,
            text="Video Settings",
            text_color=tool.Colors.WHITE,
            pos=(self.center_x - (self.btn_w // 2) - self.spacing_x, self.start_y + (self.btn_h // 2)),
            hover_text_color=tool.Colors.MC_YELLOW,
        )

        self.audio_button = ui.ImageTextButton(
            name="audio_option",
            image=assets.setting_button_img,
            text="Audio Settings",
            text_color=tool.Colors.WHITE,
            pos=(self.center_x + (self.btn_w // 2) + self.spacing_x, self.start_y + (self.btn_h // 2)),
            hover_text_color=tool.Colors.MC_YELLOW,
        )

        self.lang_button = ui.ImageTextButton(
            name="lang_option",
            image=assets.setting_button_img,
            text="Lang Settings",
            text_color=tool.Colors.WHITE,
            pos=(self.center_x - (self.btn_w // 2) - self.spacing_x, self.start_y + self.spacing_y + (self.btn_h // 2)),
            hover_text_color=tool.Colors.MC_YELLOW,
        )

        self.done_button = ui.ImageTextButton(
            name="done",
            image=assets.setting_button_img,  # 傳入你的 Minecraft 灰色按鈕圖
            text="Done",
            text_color=tool.Colors.WHITE,
            pos=(self.center_x, config.current_height - 60),
            hover_text_color=tool.Colors.MC_YELLOW,
        )

        self.all_uis = [self.video_button, self.audio_button, self.lang_button, self.done_button]

    def layout(self):
        self.video_button.rect.center = (self.center_x - (self.btn_w // 2) - self.spacing_x, self.start_y + (self.btn_h // 2))
        self.audio_button.rect.center = (self.center_x + (self.btn_w // 2) + self.spacing_x, self.start_y + (self.btn_h // 2))
        self.lang_button.rect.center = (
            self.center_x - (self.btn_w // 2) - self.spacing_x,
            self.start_y + self.spacing_y + (self.btn_h // 2),
        )
        self.done_button.rect.center = (self.center_x, config.current_height - 60)  # 👈 確保 Done 大按鈕也完美黏在底部

    def update(self, events, mouse_pos):
        self.center_x = config.current_width // 2

        for ob in self.all_uis:
            ob.update(events, mouse_pos)

        # 之後太多時放在 _handle_event裡面
        if self.done_button.is_clicked:
            config.game_state = "PAUSE"

        if self.video_button.is_clicked:
            config.game_state = "VIDEO_OPTION"

        self._handle_event(events, mouse_pos)
        self.layout()

    def _handle_event(self, events, mouse_pos):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    config.game_state = "PAUSE"

    def draw(self, screen):
        ui.show_text(screen, "Options", tool.Colors.WHITE, 0, 50, 40, screen_center=True)

        for ob in self.all_uis:
            ob.draw(screen)


class VideoMenu:
    def __init__(self):
        self.fov_value = 70  # 預設 FOV 值（Minecraft 通常是 70）
        self.fov_min = 30  # 最小值
        self.fov_max = 110  # 最大值（例如 Quake Pro 可以是 110）
        self.fov_width = assets.FOV_bg_rect.width
        self.is_dragging_fov = False  # 標記目前滑鼠是不是正在「按住拖曳拉桿」

        self.btn_w, self.btn_h = 350, 40  # 按鈕標準尺寸
        self.center_x = config.current_width // 2
        self.start_y = 150  # 從上方 150 像素開始畫按鈕
        self.spacing_x = 60  # 左右按鈕的間距
        self.spacing_y = 60  # 上下按鈕的間距

        self.fov_base = ui.ImageButton(
            name="FOV_base",  # 視野廣角
            image=assets.FOV_bg_img,
            pos=(self.center_x - (self.btn_w // 2) - self.spacing_x, self.start_y + (self.btn_h // 2)),
        )

        self.fov_lever = ui.ImageButton(
            name="FOV_lever",
            image=assets.FOV_lever_img,
            pos=(0, 0),  # 在update裡做
        )

        self.back_btn = ui.ImageTextButton(
            name="back",
            image=assets.setting_button_img,
            text="Back",
            text_color=tool.Colors.WHITE,
            pos=(self.center_x, config.current_height - 60),
            hover_text_color=tool.Colors.MC_YELLOW,
        )

        self.all_uis = [self.fov_base, self.fov_lever, self.back_btn]

    def layout(self):
        self.fov_base.rect.center = (
            self.center_x - (self.btn_w // 2) - self.spacing_x,
            self.start_y + (self.btn_h // 2),
        )
        self._update_slider()
        self.back_btn.rect.center = (self.center_x, config.current_height - 60)

    def _update_slider(self):
        self.fov_lever.rect.centery = self.fov_base.rect.centery
        lever_off = (self.fov_value - self.fov_min) / (self.fov_max - self.fov_min) * self.fov_width
        self.fov_lever.rect.centerx = self.fov_base.rect.left + lever_off

    def update(self, events, mouse_pos):
        self.center_x = config.current_width // 2

        for ob in self.all_uis:
            ob.update(events, mouse_pos)

        self._handle_event(events)
        self._update_fov(mouse_pos)

        self.layout()

    def _handle_event(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.fov_base.is_hover:
                    self.is_dragging_fov = True
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.is_dragging_fov = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    config.game_state = "OPTION"

        if self.back_btn.is_clicked:
            config.game_state = "OPTION"

    def _update_fov(self, mouse_pos):

        if self.is_dragging_fov:
            relative_x = mouse_pos[0] - self.fov_base.rect.left
            total_width = self.fov_base.rect.width

            pct = tool.clamp(0.0, 1.0, relative_x / total_width)
            fov_range = self.fov_max - self.fov_min

            self.fov_value = int(self.fov_min + pct * fov_range)
            config.fov = self.fov_value

    def draw(self, screen):
        ui.show_text(screen, "Video Options", tool.Colors.WHITE, 0, 50, 40, screen_center=True)
        for ob in self.all_uis:
            ob.draw(screen)
        ui.show_text(
            screen,
            f"FOV: {self.fov_value}",
            tool.Colors.WHITE,
            self.fov_base.rect.centerx,
            self.fov_base.rect.centery,
            center=True,
            size=30,
        )
