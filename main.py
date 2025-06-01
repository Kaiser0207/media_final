import pygame
import cv2
import numpy as np
import math
import random
import json
import os
from player import *
from boss_entities import *
from music import *
from drawing import *

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# --- 常數 ---
SCREEN_WIDTH = 1080
SCREEN_HEIGHT = 720
FPS = 60

# 顏色定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PLAYER1_COLOR = (0, 0, 255)
PLAYER1_DEAD_COLOR = (0, 0, 100)
PLAYER2_COLOR = (255, 0, 0)
PLAYER2_DEAD_COLOR = (100, 0, 0)
CHAIN_COLOR = (150, 150, 150)
LASER_WALL_COLOR = (255, 0, 255)
GOAL_P1_COLOR = (255, 100, 100)
GOAL_P2_COLOR = (100, 100, 255)
TEXT_COLOR = (200, 200, 200)
REVIVE_PROMPT_COLOR = (50, 200, 50)
COOP_BOX_COLOR = (180, 140, 0)
SCORE_FRUIT_COLOR = (255, 223, 0) #
SCORE_FRUIT_VALUE = 1 #
MAX_TOTAL_SCORE = 3 #
MENU_OPTION_COLOR = (220, 220, 220) # NEW
MENU_SELECTED_OPTION_COLOR = (255, 255, 0) # NEW
PAUSE_OVERLAY_COLOR = (0, 0, 0, 150) # NEW

LEADERBOARD_FILE = "leaderboard.json"
MAX_LEADERBOARD_ENTRIES = 10 # Show top 10
FACE_IMAGE_SAVE_DIR = "CatchFace"
LEADERBOARD_FACE_SIZE = (60, 60) # Individual face size

# 玩家參數
CHAIN_MAX_LENGTH = 400 #
CHAIN_ITERATIONS = 5 #
REVIVAL_RADIUS = CHAIN_MAX_LENGTH #
REVIVE_KEYP1 = pygame.K_f #
REVIVE_KEYP2 = pygame.K_PERIOD #

# 協力推箱子常數
COOP_BOX_SIZE = 40 #
COOP_BOX_SPEED = 2 #
COOP_BOX_PUSH_RADIUS = 60 #

# 地刺參數
SAFE_COLOR = (220, 220, 220) #
DANGER_COLOR = (220, 40, 40) #

# 遊戲狀態
STATE_START_SCREEN = 4 #
STATE_PLAYING = 0 #
STATE_GAME_OVER = 1 #
STATE_LEVEL_COMPLETE = 2 # No longer used directly for "all levels", see PRE_BOSS
STATE_PRE_BOSS_COMPLETE = 3 # This state will no longer be actively used for a waiting screen
STATE_BOSS_LEVEL = 5 # New state for Boss Level #
STATE_BOSS_DEFEATED = 6 # New state for when Boss is defeated
STATE_ASK_CAMERA = 9
STATE_CAMERA_INPUT = 7
STATE_SHOW_LEADERBOARD = 8
STATE_PAUSED = 10 # NEW: Pause Menu State
STATE_LEVEL_SELECT = 11 # NEW: Level Selection State

# --- 果實相關常數 ---
FRUIT_RADIUS = 15 #
FRUIT_EFFECT_DURATION = 30.0 #

# 果實顏色
MIRROR_FRUIT_COLOR = (255, 215, 0) #
INVISIBLE_WALL_COLOR = (138, 43, 226) #
VOLCANO_FRUIT_COLOR = (255, 69, 0) #

# 火山效果相關常數
METEOR_WARNING_TIME = 1.5 #
METEOR_FALL_TIME = 0.5 #
METEOR_SIZE = 75 #
METEOR_COLOR = (139, 69, 19) #
WARNING_COLOR = (255, 255, 0) #

# Boss Level Item Spawn Point (P2 "draws" here if P1 not available)
ITEM_SPAWN_POS_DEFAULT = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50) #

# --- 檔案相關 ---
SAVE_FILE = "savegame.json"
SAVE_MESSAGE_COLOR = (255, 0, 0)
show_save_feedback = False
save_feedback_timer = 0.0
SAVE_FEEDBACK_DURATION = 2.0

# --- Pygame 初始化 ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("雙人合作遊戲 Demo - 果實能力 & Boss") # Updated Caption
clock = pygame.time.Clock()
if not os.path.exists(FACE_IMAGE_SAVE_DIR):
    os.makedirs(FACE_IMAGE_SAVE_DIR)

default_face_image_surface = None
try:
    profile_jpg_path = os.path.join(FACE_IMAGE_SAVE_DIR, "PROFILE.jpg")
    absolute_profile_jpg_path = os.path.normpath(os.path.join(SCRIPT_DIR, profile_jpg_path))

    raw_default_face = pygame.image.load(absolute_profile_jpg_path).convert_alpha()
    default_face_image_surface = pygame.transform.scale(raw_default_face, LEADERBOARD_FACE_SIZE)
    print("PROFILE.jpg 已成功從 CatchFace 資料夾載入並縮放。")
except pygame.error as e:
    print(f"警告：無法載入 PROFILE.jpg: {e}。將使用預留位置顏色。")
    default_face_image_surface = None

# --- 音樂檔案路徑 ---
LEVEL_1_MUSIC = os.path.join("game_music", "04 - Silent Forest.mp3") #
BOSS_MUSIC = os.path.join("game_music", "10 - Lost Shrine.mp3") #
FINAL_BATTLE_MUSIC = os.path.join("game_music", "21 - Final Battle - For Love.mp3") #

# 圖片載入
box_img = pygame.image.load("box.png").convert_alpha() #
spike_trap_img_out = pygame.image.load("spike_trap_out.png").convert_alpha() #
spike_trap_img_in = pygame.image.load("spike_trap_in.png").convert_alpha() #

# 載入 floor.png 作為平鋪背景
floor_tile = pygame.image.load(os.path.join('plays_animation_art', 'floor.png')).convert_alpha()
floor_tile_width, floor_tile_height = floor_tile.get_width(), floor_tile.get_height()

# 新增：載入 floor_ladder.png 作為 boss_defeated_area_rect 圖像
floor_ladder_img = pygame.image.load(os.path.join('plays_animation_art', 'floor_ladder.png')).convert_alpha()
floor_ladder_width, floor_ladder_height = floor_ladder_img.get_width(), floor_ladder_img.get_height()

# 加載支持中文的字體 (Copied from original)
try:
    system_fonts = pygame.font.get_fonts()
    chinese_font_name = None
    possible_chinese_fonts = [
        'microsoftyahei', 'msyh', 'simsun', 'simhei', 'noto sans cjk tc',
        'noto sans cjk sc', 'microsoft jhenghei', 'pmingliu', 'kaiti', 'heiti tc',
        'heiti sc', 'droid sans fallback'
    ]
    for font in possible_chinese_fonts:
        if font in system_fonts or font.replace(' ', '') in system_fonts:
            chinese_font_name = font
            break
    if chinese_font_name:
        font_path = pygame.font.match_font(chinese_font_name)
        font_small = pygame.font.Font(font_path, 36)
        font_large = pygame.font.Font(font_path, 74)
        font_tiny = pygame.font.Font(font_path, 24)
        font_effect = pygame.font.Font(font_path, 18)
        font_menu = pygame.font.Font(font_path, 48) # NEW: For menus
    else:
        print("警告：找不到中文字體，遊戲中的中文可能無法正確顯示")
        font_small = pygame.font.Font(None, 36)
        font_large = pygame.font.Font(None, 74)
        font_tiny = pygame.font.Font(None, 24)
        font_effect = pygame.font.Font(None, 18)
        font_menu = pygame.font.Font(None, 48) # NEW: For menus
except Exception as e:
    print(f"載入字體時出錯：{e}")
    font_small = pygame.font.Font(None, 36)
    font_large = pygame.font.Font(None, 74)
    font_tiny = pygame.font.Font(None, 24)
    font_effect = pygame.font.Font(None, 18)
    font_menu = pygame.font.Font(None, 48) # NEW: For menus

# --- OpenCV 視窗準備 (Not used by fruits) ---
use_opencv = False #
opencv_window_name = "P2 Paint Area (OpenCV)" #
paint_surface_width = 400 #
paint_surface_height = 300 #
paint_surface = np.zeros((paint_surface_height, paint_surface_width, 3), dtype=np.uint8) + 200 #

# --- Global game variables ---
game_time_elapsed = 0.0
current_score = 0
leaderboard_data = []
final_game_time = 0.0
final_player_score = 0

# Variables for camera input state
camera_capture_active = False
player_name_input_active = False # For single entry/team name
current_player_name = "" # Single entry/team name
captured_face_image_path_p1 = None
captured_face_image_path_p2 = None
current_capture_player_index = 0 # 0 for P1, 1 for P2
photo_taken_for_current_player_flag = False # Flag if photo was taken/skipped for current player_capture_index
post_capture_prompt_active = False # If true, shows options after a capture/skip attempt


# OpenCV related
cap = None
face_cascade = None
camera_frame_surface = None # Pygame surface for camera feed
loaded_face_images_cache = {} # Cache for loaded face images for leaderboard

boss_music_playing = False # 追蹤BOSS_MUSIC是否正在播放

state_before_pause = None
pause_menu_options = [
    "繼續遊戲",
    "重新開始關卡",
    "儲存遊戲",
    "載入遊戲",
    "回到主選單",
    "離開遊戲"
]
pause_menu_selected_index = 0


level_select_options = [] # Will be populated
level_select_selected_index = 0

start_menu_options = [
    "開始新遊戲",
    "選擇關卡",
    "載入遊戲",
    "查看排行榜",
    "離開遊戲"
]
start_menu_selected_index = 0

leaderboard_menu_options = [
    ("重新開始", "RESTART"),
    ("返回主選單", "MAIN_MENU"),
    ("離開遊戲", "QUIT")
]
leaderboard_menu_selected_index = 0

def show_opencv_paint_window(): #
    if use_opencv:
        cv2.imshow(opencv_window_name, paint_surface)
        key = cv2.waitKey(1) & 0xFF

# --- 果實類別 --- (Copied from original)
class Fruit(pygame.sprite.Sprite):
    def __init__(self, x, y, fruit_type):
        super().__init__()
        self.fruit_type = fruit_type
        if fruit_type == "volcano":
            img = pygame.image.load('./plays_animation_art/book_1.png').convert_alpha()
            img = pygame.transform.smoothscale(img, (FRUIT_RADIUS * 2, FRUIT_RADIUS * 2))
            self.image = img
        elif fruit_type == "invisible_wall":
            img = pygame.image.load('./plays_animation_art/book_2.png').convert_alpha()
            img = pygame.transform.smoothscale(img, (FRUIT_RADIUS * 2, FRUIT_RADIUS * 2))
            self.image = img
        elif fruit_type == "mirror":
            img = pygame.image.load('./plays_animation_art/book_3.png').convert_alpha()
            img = pygame.transform.smoothscale(img, (FRUIT_RADIUS * 2, FRUIT_RADIUS * 2))
            self.image = img
        else:
            self.image = pygame.Surface([FRUIT_RADIUS * 2, FRUIT_RADIUS * 2], pygame.SRCALPHA)
            color = (255, 255, 255)
            pygame.draw.circle(self.image, color, (FRUIT_RADIUS, FRUIT_RADIUS), FRUIT_RADIUS)
            pygame.draw.circle(self.image, WHITE, (FRUIT_RADIUS, FRUIT_RADIUS), FRUIT_RADIUS, 2)
        self.rect = self.image.get_rect(center=(x, y))

# --- 流星類別 (火山爆發效果) --- (Copied from original)
class Meteor(pygame.sprite.Sprite): #
    def __init__(self, x, y, lifetime=METEOR_FALL_TIME):
        super().__init__()
        self.image = pygame.Surface([METEOR_SIZE, METEOR_SIZE], pygame.SRCALPHA)
        pygame.draw.circle(self.image, METEOR_COLOR, (METEOR_SIZE // 2, METEOR_SIZE // 2), METEOR_SIZE // 2)
        pygame.draw.ellipse(self.image, (0, 0, 0, 100), [0, 0, METEOR_SIZE, METEOR_SIZE], 2)
        self.rect = self.image.get_rect(center=(x, y))
        self.active = True
        self.lifetime = lifetime
        self.timer = 0

    def update(self, dt):
        self.timer += dt
        if self.timer >= self.lifetime: self.kill()

# --- 警告標記類別 --- (Copied from original)
class Warning(pygame.sprite.Sprite): #
    def __init__(self, x, y, duration):
        super().__init__()
        self.image = pygame.Surface([METEOR_SIZE * 1.5, METEOR_SIZE * 1.5], pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
        self.duration = duration
        self.timer = 0
        self.spawn_pos = (x, y)

    def update(self, dt):
        self.timer += dt
        flash_speed = 10
        alpha = int(159 + 96 * math.sin(self.timer * flash_speed))
        self.image.fill((0, 0, 0, 0))
        pygame.draw.circle(self.image, WARNING_COLOR + (alpha,), (self.rect.width // 2, self.rect.height // 2),
                           int(METEOR_SIZE * 0.75), 3)
        if self.timer >= self.duration:
            self.kill()
            return True # Indicate meteor should spawn
        return False

# --- 效果管理器 --- (Copied from original)
class EffectManager: #
    def __init__(self):
        self.default_laser_wall_alpha = 255
        self.effects = {
            "mirror_p1": {"active": False, "timer": 0, "name": "P1 反向"},
            "mirror_p2": {"active": False, "timer": 0, "name": "P2 反向"},
            "invisible_wall": {"active": False, "timer": 0, "flash_timer": 0,
                               "current_alpha": self.default_laser_wall_alpha, "name": "牆壁隱形"},
            "volcano": {"active": False, "timer": 0, "meteor_timer": 0, "name": "火山爆發"}
        }

    def apply_effect(self, effect_type, player_id=None):
        if effect_type == "mirror":
            if player_id == 0:
                self.effects["mirror_p1"]["active"] = True;
                self.effects["mirror_p1"]["timer"] = FRUIT_EFFECT_DURATION
            elif player_id == 1:
                self.effects["mirror_p2"]["active"] = True;
                self.effects["mirror_p2"]["timer"] = FRUIT_EFFECT_DURATION
        elif effect_type == "invisible_wall":
            self.effects["invisible_wall"]["active"] = True;
            self.effects["invisible_wall"]["timer"] = FRUIT_EFFECT_DURATION
            self.effects["invisible_wall"]["flash_timer"] = 0;
            self.effects["invisible_wall"]["current_alpha"] = 0
        elif effect_type == "volcano":
            self.effects["volcano"]["active"] = True;
            self.effects["volcano"]["timer"] = FRUIT_EFFECT_DURATION
            self.effects["volcano"]["meteor_timer"] = 0

    def update(self, dt):
        for key in ["mirror_p1", "mirror_p2"]:
            if self.effects[key]["active"]: self.effects[key]["timer"] -= dt
            if self.effects[key]["timer"] <= 0: self.effects[key]["active"] = False
        if self.effects["invisible_wall"]["active"]:
            self.effects["invisible_wall"]["timer"] -= dt;
            self.effects["invisible_wall"]["flash_timer"] += dt
            target_alpha = 0
            if self.effects["invisible_wall"]["timer"] <= 0:
                self.effects["invisible_wall"]["active"] = False;
                self.effects["invisible_wall"]["current_alpha"] = self.default_laser_wall_alpha
            else:
                cycle_duration = 5.0;
                hidden_duration = 4.0;
                visible_duration = 1.0;
                fade_time = visible_duration / 2
                current_cycle_time = self.effects["invisible_wall"]["flash_timer"] % cycle_duration
                if current_cycle_time < hidden_duration:
                    target_alpha = 0
                else:
                    time_in_visible_phase = current_cycle_time - hidden_duration
                    if time_in_visible_phase < fade_time:
                        target_alpha = int((time_in_visible_phase / fade_time) * 255)
                    else:
                        time_in_fade_out = time_in_visible_phase - fade_time;
                        target_alpha = int(
                            (1.0 - (time_in_fade_out / fade_time)) * 255)
                self.effects["invisible_wall"]["current_alpha"] = max(0, min(255, target_alpha))
        else:
            if self.effects["invisible_wall"]["current_alpha"] != self.default_laser_wall_alpha:
                self.effects["invisible_wall"]["current_alpha"] = self.default_laser_wall_alpha

        if self.effects["volcano"]["active"]:
            self.effects["volcano"]["timer"] -= dt;
            self.effects["volcano"]["meteor_timer"] += dt
            if self.effects["volcano"]["timer"] <= 0: self.effects["volcano"]["active"] = False

    def get_laser_wall_alpha(self):
        if self.effects["invisible_wall"]["active"]: return self.effects["invisible_wall"]["current_alpha"]
        return self.default_laser_wall_alpha

    def is_mirror_active(self, player_id):
        if player_id == 0:
            return self.effects["mirror_p1"]["active"]
        elif player_id == 1:
            return self.effects["mirror_p2"]["active"]
        return False

    def should_spawn_meteor(self):
        return (self.effects["volcano"]["active"] and self.effects["volcano"]["meteor_timer"] >= random.uniform(0.6,
                                                                                                                1.2))

    def reset_meteor_timer(self):
        self.effects["volcano"]["meteor_timer"] = 0

    def reset_all_effects(self):
        for effect_key in self.effects:
            self.effects[effect_key]["active"] = False;
            self.effects[effect_key]["timer"] = 0
            if "flash_timer" in self.effects[effect_key]: self.effects[effect_key]["flash_timer"] = 0
            if "showing" in self.effects[effect_key]: self.effects[effect_key]["showing"] = True
            if "meteor_timer" in self.effects[effect_key]: self.effects[effect_key]["meteor_timer"] = 0
            if effect_key == "invisible_wall": self.effects[effect_key]["current_alpha"] = self.default_laser_wall_alpha

    def get_active_effects_info(self):
        info = []
        for key, data in self.effects.items():
            if data["active"]: info.append(f"{data['name']}: {data['timer']:.1f}s")
        return info

# --- 牆壁類別 (雷射牆壁) --- (Copied from original)
class LaserWall(pygame.sprite.Sprite): #
    def __init__(self, x, y, width, height):
        super().__init__()
        self.original_color = LASER_WALL_COLOR
        self.image = pygame.Surface([width, height], pygame.SRCALPHA)
        self.image.fill((self.original_color[0], self.original_color[1], self.original_color[2], 255))
        self.rect = self.image.get_rect(topleft=(x, y))
        self._current_alpha = 255

    def update_visuals(self, alpha_value):
        alpha_value = max(0, min(255, int(alpha_value)))
        if self._current_alpha != alpha_value:
            self._current_alpha = alpha_value
            self.image.fill(
                (self.original_color[0], self.original_color[1], self.original_color[2], self._current_alpha))

# --- 目標類別 (顏色地板) --- (Copied from original)
class Goal(pygame.sprite.Sprite): #
    def __init__(self, x, y, color, player_id_target):
        super().__init__()
        self.image = pygame.Surface([int(PLAYER_RADIUS * 2.5), int(PLAYER_RADIUS * 2.5)])
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        self.player_id_target = player_id_target
        self.is_active = False

    def update_status(self, player):
        if player.is_alive and self.rect.colliderect(player.rect) and player.player_id == self.player_id_target:
            self.is_active = True
        else:
            self.is_active = False

    def draw(self, surface):
        surface.blit(self.image, self.rect)
        if self.is_active: pygame.draw.rect(surface, WHITE, self.rect, 3)

# --- 協力推箱子類別 --- (Copied from original)
class CoopBox(pygame.sprite.Sprite): #
    def __init__(self, x, y, img=None):
        super().__init__()
        self.collision_size = COOP_BOX_SIZE;
        self.display_size = 60
        self.rect = pygame.Rect(0, 0, self.collision_size, self.collision_size);
        self.rect.center = (x, y)
        self.pos = pygame.math.Vector2(x, y)
        if img:
            self.image = pygame.transform.scale(img, (self.display_size, self.display_size))
        else:
            self.image = pygame.Surface([self.display_size, self.displaySize]);
            self.image.fill(COOP_BOX_COLOR)

    def move(self, direction, obstacles):
        tentative_pos = self.pos + direction * COOP_BOX_SPEED;
        test_rect = self.rect.copy();
        test_rect.center = tentative_pos
        for obs in obstacles:
            if test_rect.colliderect(obs.rect) and isinstance(obs, LaserWall): return
        if not (self.collision_size // 2 <= tentative_pos.x <= SCREEN_WIDTH - self.collision_size // 2 and \
                self.collision_size // 2 <= tentative_pos.y <= SCREEN_HEIGHT - self.collision_size // 2): return
        self.pos = tentative_pos;
        self.rect.center = self.pos

    def draw(self, surface):
        img_rect = self.image.get_rect(center=self.rect.center);
        surface.blit(self.image, img_rect)

# ---地刺類別--- (Copied from original)
class SpikeTrap(pygame.sprite.Sprite): #
    def __init__(self, x, y, width=40, height=40, out_time=1.0, in_time=1.5, phase_offset=0.0, img_out=None,
                 img_in=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height);
        self.out_time = out_time;
        self.in_time = in_time
        self.cycle_time = self.out_time + self.in_time;
        self.timer = phase_offset;
        self.active = False
        self.img_out = img_out;
        self.img_in = img_in

    def update(self, dt):
        self.timer += dt;
        phase = self.timer % self.cycle_time;
        self.active = phase < self.out_time

    def is_dangerous(self):
        return self.active

    def draw(self, surface):
        current_img = None
        if self.active and self.img_out:
            current_img = self.img_out
        elif not self.active and self.img_in:
            current_img = self.img_in
        if current_img:
            surface.blit(pygame.transform.scale(current_img, (self.rect.width, self.rect.height)), self.rect)
        else:
            pygame.draw.rect(surface, DANGER_COLOR if self.active else SAFE_COLOR, self.rect)


# --- 關卡資料 ---
levels_data = [ #
    { # Level 1 Data (existing)
        "player1_start": (100, SCREEN_HEIGHT // 2), "player2_start": (150, SCREEN_HEIGHT // 2),
        "goal1_pos": (SCREEN_WIDTH - 50, 150), "goal2_pos": (SCREEN_WIDTH - 50, SCREEN_HEIGHT - 150),
        "laser_walls": [(SCREEN_WIDTH // 2 - 10, 150, 20, SCREEN_HEIGHT - 300),
                        (200, SCREEN_HEIGHT // 2 - 10, SCREEN_WIDTH // 2 - 200 - 10, 20),
                        (SCREEN_WIDTH // 2 + 10, SCREEN_HEIGHT // 2 - 10, SCREEN_WIDTH // 2 - 20 - 10, 20)],
        "coop_box_start": [(SCREEN_WIDTH // 4, SCREEN_HEIGHT // 4), (SCREEN_WIDTH // 4 + 50, SCREEN_HEIGHT // 4 + 50)],
        "spike_traps": [(100, 540, 40, 40, 1.0, 2.0, 0.0), (160, 540, 40, 40, 0.7, 1.5, 0.5),
                        (220, 540, 40, 40, 1.2, 1.0, 1.0)],
        "fruits": [(SCREEN_WIDTH - 220, SCREEN_HEIGHT - 200, "mirror"),
                   (SCREEN_WIDTH - 260, SCREEN_HEIGHT - 200, "invisible_wall"),
                   (SCREEN_WIDTH - 300, SCREEN_HEIGHT - 200, "volcano")]
    },
    { # Level 2 Data (existing)
        "player1_start": (50, 50), "player2_start": (100, 50),
        "goal1_pos": (200, SCREEN_HEIGHT - 100), "goal2_pos": (200, SCREEN_HEIGHT - 50),
        "laser_walls": [(0, 0, SCREEN_WIDTH, 20), (0, SCREEN_HEIGHT - 20, SCREEN_WIDTH, 20), (0, 0, 20, SCREEN_HEIGHT),
                        (SCREEN_WIDTH - 20, 0, 20, SCREEN_HEIGHT), (150, 20, 20, SCREEN_HEIGHT // 2 - 25),
                        (150, SCREEN_HEIGHT // 2 + 50, 20, SCREEN_HEIGHT // 2 - 95),
                        (SCREEN_WIDTH - 150, 20, 20, SCREEN_HEIGHT // 2 - 100),
                        (SCREEN_WIDTH - 150, SCREEN_HEIGHT // 2, 20, SCREEN_HEIGHT // 2 - 100),
                        (150, SCREEN_HEIGHT // 3, SCREEN_WIDTH - 300, 20),
                        (150, SCREEN_HEIGHT * 2 // 3, SCREEN_WIDTH - 300, 20)],
        "coop_box_start": [(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)],
        "fruits": [(160, SCREEN_HEIGHT // 2 + 20, "volcano"), (SCREEN_WIDTH - 140, SCREEN_HEIGHT // 2 - 30, "mirror"),
                   (SCREEN_WIDTH - 140, SCREEN_HEIGHT - 60, "invisible_wall")]
    },
    {
        "player1_start": (40, SCREEN_HEIGHT // 2 + 70), "player2_start": (40, SCREEN_HEIGHT // 2 - 50),
        "goal1_pos": (SCREEN_WIDTH - 50, 190), "goal2_pos": (SCREEN_WIDTH - 50, SCREEN_HEIGHT - 190),
        "laser_walls": [ # 衡的外面
            (0, 100, 550, 20), (0, SCREEN_HEIGHT - 100, 550, 20),
            (600, 100, 150, 20), (600, SCREEN_HEIGHT - 100, 150, 20),
            (800, 100, 90, 20), (800, SCREEN_HEIGHT - 100, 100, 20),
            # 值得裡面
            (80, 120, 20, 150), (80, SCREEN_HEIGHT - 260, 20, 180),
            (180, 210, 20, 150), (180, SCREEN_HEIGHT - 340, 20, 180),
            (280, 120, 20, 150), (280, SCREEN_HEIGHT - 260, 20, 180),
            (380, 210, 20, 150), (380, SCREEN_HEIGHT - 340, 20, 180),
            (480, 80, 20, 180), (480, SCREEN_HEIGHT - 250, 20, 180),

            # 終點乓圈圈
            (980, 330, 100, 20), (980, SCREEN_HEIGHT - 330, 150, 20),
            (950, 150, 20, 150), (950, SCREEN_HEIGHT - 300, 20, 150),

            (850, 220, 20, 150), (850, SCREEN_HEIGHT - 350, 20, 180),

            (650, SCREEN_HEIGHT // 2 -140, 20, 300),

            (750, 100, 20, 220), (750, SCREEN_HEIGHT - 300, 20, 220),
            (0, SCREEN_HEIGHT // 2, 500, 20)],
        "coop_box_start": [(1010, 120), (1050, 120), (SCREEN_WIDTH - 70, SCREEN_HEIGHT - 120),
                           (SCREEN_WIDTH - 30, SCREEN_HEIGHT - 120)],
        "spike_traps": [(750, 325, 40, 40, 1.5, 2.5, 0.0), (750, 365, 40, 40, 1.5, 2.5, 0.0),
                        (75, 300, 40, 40, 1.5, 2.5, 1.5), (175, 570, 40, 40, 1.5, 2.5, 0.4),
                        (275, 300, 40, 40, 1.5, 2.5, 0.3), (375, 570, 40, 40, 1.5, 2.5, 1.6),
                        (475, 300, 40, 40, 1.5, 2.5, 2.5), (475, 400, 40, 40, 1.5, 2.5, 0.5),
                        (40, 40, 40, 40, 1.0, 2.0, 0.0), (100, 40, 40, 40, 0.7, 1.5, 0.5),
                        (160, 40, 40, 40, 1.2, 1.0, 1.0)],
        "fruits": [(SCREEN_WIDTH - 260, SCREEN_HEIGHT - 180, "mirror"),
                   (40,  200, "invisible_wall"),
                   (SCREEN_WIDTH - 500, SCREEN_HEIGHT - 350, "volcano")]
    },
    # Boss level will be handled separately, not in this list structure.
]
current_level_index = 0 #

# --- 遊戲物件群組 ---
all_sprites = pygame.sprite.Group() #
laser_wall_sprites = pygame.sprite.Group() #
goal_sprites = pygame.sprite.Group() #
player_sprites = pygame.sprite.Group() #
coop_box_group = pygame.sprite.Group() #
spike_trap_group = pygame.sprite.Group() #
fruit_sprites = pygame.sprite.Group() #
meteor_sprites = pygame.sprite.Group() #
warning_sprites = pygame.sprite.Group() #

# Boss Level Specific Groups
boss_group = pygame.sprite.GroupSingle() # For single boss
throwable_objects_group = pygame.sprite.Group() #
# boss_projectiles are managed within the Boss class instance's group

# --- 遊戲物件實體 ---
player1 = Player(0, 0, PLAYER1_COLOR, PLAYER1_DEAD_COLOR,
                 {'up': pygame.K_w, 'down': pygame.K_s, 'left': pygame.K_a, 'right': pygame.K_d}, 0) #
player2 = Player(0, 0, PLAYER2_COLOR, PLAYER2_DEAD_COLOR,
                 {'up': pygame.K_UP, 'down': pygame.K_DOWN, 'left': pygame.K_LEFT, 'right': pygame.K_RIGHT}, 1) #
player_sprites.add(player1, player2)

goal1 = Goal(0, 0, GOAL_P1_COLOR, 0) #
goal2 = Goal(0, 0, GOAL_P2_COLOR, 1) #
# coop_box is loaded per level

effect_manager = EffectManager() #
boss_enemy = None # Will be initialized for boss level

# 新增 Boss 被擊敗後的區域
boss_defeated_area_rect = None

def load_leaderboard():
    global leaderboard_data, loaded_face_images_cache
    loaded_face_images_cache.clear() # Clear cache when reloading leaderboard
    try:
        with open(LEADERBOARD_FILE, 'r') as f:
            leaderboard_data = json.load(f)
    except FileNotFoundError:
        leaderboard_data = []
    except json.JSONDecodeError:
        leaderboard_data = []
        print(f"Warning: {LEADERBOARD_FILE} is corrupted or invalid. Starting with an empty leaderboard.")

def save_leaderboard():
    global leaderboard_data
    leaderboard_data.sort(key=lambda x: (x.get('time', float('inf')), -x.get('score', 0)))
    leaderboard_data = leaderboard_data[:MAX_LEADERBOARD_ENTRIES]
    try:
        with open(LEADERBOARD_FILE, 'w') as f:
            json.dump(leaderboard_data, f, indent=4)
    except Exception as e:
        print(f"Error saving leaderboard: {e}")


def add_leaderboard_entry(name, time_val, score_val, image_path_p1, image_path_p2): # MODIFIED
    global leaderboard_data
    leaderboard_data.append({
        "name": name, # Team/entry name
        "time": round(time_val, 2),
        "score": score_val,
        "face_image_path_p1": image_path_p1, # MODIFIED
        "face_image_path_p2": image_path_p2 # MODIFIED
    })

load_leaderboard() # Load at game start

def initialize_camera_for_capture():
    global cap, face_cascade, camera_capture_active, game_state
    if cap and cap.isOpened():
        camera_capture_active = True
        return

    try:
        pictPath = cv2.data.haarcascades + 'haarcascade_frontalface_alt2.xml'
        if not os.path.exists(pictPath):
            print(f"錯誤：找不到 Haar cascade 檔案於 {pictPath}")
            game_state = STATE_SHOW_LEADERBOARD # Fallback
            return

        face_cascade = cv2.CascadeClassifier(pictPath)
        if face_cascade.empty():
            print("錯誤：無法載入 Haar cascade。")
            game_state = STATE_SHOW_LEADERBOARD # Fallback
            return

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("錯誤：無法開啟攝影機。")
            cap = None
            game_state = STATE_SHOW_LEADERBOARD # Fallback
            return
        camera_capture_active = True
        print("攝影機已初始化。")
    except Exception as e:
        print(f"攝影機初始化時發生例外狀況：{e}")
        release_camera_resources()
        game_state = STATE_SHOW_LEADERBOARD # Fallback

def release_camera_resources():
    global cap, camera_capture_active, camera_frame_surface
    if cap:
        cap.release()
        cap = None
    camera_capture_active = False
    camera_frame_surface = None
    # cv2.destroyAllWindows() # Keep OpenCV windows managed by their own logic if 'use_opencv' is true elsewhere
    print("攝影機資源已釋放。")

def process_camera_frame():
    global cap, face_cascade, camera_frame_surface, game_state
    if not camera_capture_active or not cap or not cap.isOpened() or not face_cascade:
        return

    ret, frame_bgr = cap.read()
    if not ret:
        print("錯誤：無法從攝影機讀取畫面。")
        # release_camera_resources() # Don't release here, allow retry
        # game_state = STATE_SHOW_LEADERBOARD
        return

    frame_bgr = cv2.flip(frame_bgr, 1)
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    # Detect all faces, let handle_photo_capture decide which one if multiple are very close
    # For sequential capture, we primarily care if *a* face is detected for the current player.
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))

    display_frame_bgr = frame_bgr.copy()
    for (x, y, w, h) in faces: # Draw on all detected faces for preview
        cv2.rectangle(display_frame_bgr, (x, y), (x + w, y + h), (0, 255, 0), 2)

    frame_rgb = cv2.cvtColor(display_frame_bgr, cv2.COLOR_BGR2RGB)
    target_width, target_height = min(640, SCREEN_WIDTH - 100), min(480, SCREEN_HEIGHT - 200)
    frame_resized = cv2.resize(frame_rgb, (target_width, target_height))
    temp_surface = pygame.surfarray.make_surface(frame_resized)
    camera_frame_surface = pygame.transform.rotate(temp_surface, -90)

def handle_photo_capture(player_capture_idx): # player_capture_idx: 0 for P1, 1 for P2
    global cap, face_cascade, current_player_name # Entry/Team name
    global captured_face_image_path_p1, captured_face_image_path_p2
    global post_capture_prompt_active # Renamed from photo_taken_prompt_active

    if not camera_capture_active or not cap or not cap.isOpened() or not face_cascade:
        post_capture_prompt_active = True # Go to prompt to allow retry/skip
        return False

    ret, frame_bgr = cap.read()
    if not ret:
        print("拍照錯誤：無法讀取畫面。")
        post_capture_prompt_active = True
        return False
    frame_bgr = cv2.flip(frame_bgr, 1)

    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))

    if len(faces) > 0:
        x, y, w, h = faces[0] # Capture the first detected face
        face_crop = frame_bgr[y:y + h, x:x + w]
        face_resize = cv2.resize(face_crop, LEADERBOARD_FACE_SIZE)

        sane_name = "".join(c if c.isalnum() else "_" for c in current_player_name.strip())
        if not sane_name: sane_name = "entry" # Default for entry/team name part of filename

        current_image_path_to_delete = None
        filename_suffix = ""
        if player_capture_idx == 0:
            current_image_path_to_delete = captured_face_image_path_p1
            filename_suffix = "_p1"
        else: # player_capture_idx == 1
            current_image_path_to_delete = captured_face_image_path_p2
            filename_suffix = "_p2"

        index = 1
        # Filename: entryname_pX_idx.png
        base_filename_template = os.path.join(FACE_IMAGE_SAVE_DIR, f"{sane_name}{filename_suffix}_{{}}.png")
        new_image_path = base_filename_template.format(index)
        while os.path.exists(new_image_path):
            index += 1
            new_image_path = base_filename_template.format(index)

        try:
            if current_image_path_to_delete and os.path.exists(current_image_path_to_delete):
                os.remove(current_image_path_to_delete)
                print(f"已刪除玩家 {player_capture_idx + 1} 的舊照片: {current_image_path_to_delete}")

            cv2.imwrite(new_image_path, face_resize)
            print(f"玩家 {player_capture_idx + 1} 的臉部影像已儲存至 {new_image_path}")

            if player_capture_idx == 0:
                captured_face_image_path_p1 = new_image_path
            else:
                captured_face_image_path_p2 = new_image_path

            post_capture_prompt_active = True
            return True
        except Exception as e:
            print(f"儲存玩家 {player_capture_idx + 1} 的影像時發生錯誤: {e}")
            # Restore old path if save failed, so it can be potentially deleted on a successful retry
            if player_capture_idx == 0:
                captured_face_image_path_p1 = current_image_path_to_delete
            else:
                captured_face_image_path_p2 = current_image_path_to_delete
            post_capture_prompt_active = True
            return False
    else:
        print(f"未偵測到玩家 {player_capture_idx + 1} 的臉部。")
        post_capture_prompt_active = True
        return False

# --- Boss Level Setup Function ---
def setup_boss_level():
    global boss_enemy, game_state, game_time_elapsed, current_score # Added current_score for consistency
    # 播放Boss關卡音樂
    play_music(BOSS_MUSIC) #
    # Clear regular level sprites if any could persist (though load_level should handle most)
    laser_wall_sprites.empty()
    goal_sprites.empty()
    coop_box_group.empty()
    spike_trap_group.empty()
    fruit_sprites.empty() # No fruits in boss level by default
    meteor_sprites.empty()
    warning_sprites.empty()
    throwable_objects_group.empty() # Clear any previous throwable items
    effect_manager.reset_all_effects() # Reset any active fruit effects
    # Reset players to starting positions for boss arena
    player1.start_pos = pygame.math.Vector2(100, SCREEN_HEIGHT - 100)
    player2.start_pos = pygame.math.Vector2(150, SCREEN_HEIGHT - 100)
    player1.reset()
    player2.reset()

    # Initialize Boss
    boss_enemy = Boss(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4) #
    boss_group.add(boss_enemy)

    # No laser walls, goals, coop boxes, spikes in this basic boss level setup. Can be added if needed.
    game_state = STATE_BOSS_LEVEL

def load_level(level_idx): #
    global game_state, current_level_index, game_time_elapsed, current_score# Added game_time_elapsed, current_score reset
    if level_idx >= len(levels_data):
        setup_boss_level() # Directly set up the boss level if all regular levels are done
        return

    level = levels_data[level_idx]
    current_level_index = level_idx # Keep track of the actual level number being played

    play_music(LEVEL_1_MUSIC) #

    laser_wall_sprites.empty();
    goal_sprites.empty();
    coop_box_group.empty()
    spike_trap_group.empty();
    fruit_sprites.empty();
    meteor_sprites.empty();
    warning_sprites.empty();
    throwable_objects_group.empty() # Clear throwable from previous attempts
    effect_manager.reset_all_effects()
    game_time_elapsed = 0.0 # Reset timer for new regular level
    current_score = 0 # Reset score for new regular level

    player1.start_pos = pygame.math.Vector2(level["player1_start"])
    player2.start_pos = pygame.math.Vector2(level["player2_start"])
    player1.reset();
    player2.reset()

    for lw_data in level["laser_walls"]: laser_wall_sprites.add(LaserWall(*lw_data))
    goal1.rect.center = level["goal1_pos"];
    goal2.rect.center = level["goal2_pos"]
    goal1.is_active = False;
    goal2.is_active = False;
    goal_sprites.add(goal1, goal2)

    coop_box_starts = level.get("coop_box_start", [])
    if coop_box_starts:
        if isinstance(coop_box_starts[0], (list, tuple)) and not isinstance(coop_box_starts[0], int):
            for pos_data in coop_box_starts:
                if len(pos_data) == 2: coop_box_group.add(CoopBox(pos_data[0], pos_data[1], img=box_img))
        elif len(coop_box_starts) == 2 and isinstance(coop_box_starts[0], (int, float)):
            coop_box_group.add(CoopBox(coop_box_starts[0], coop_box_starts[1], img=box_img))

    for spike_data in level.get("spike_traps", []): spike_trap_group.add(
        SpikeTrap(*spike_data, img_out=spike_trap_img_out, img_in=spike_trap_img_in))

    obstacle_sprites_for_fruits = pygame.sprite.Group(laser_wall_sprites.sprites(), spike_trap_group.sprites(),
                                                      coop_box_group.sprites(), goal_sprites.sprites())
    for fruit_data in level.get("fruits", []):
        fx, fy, ftype = fruit_data;
        original_pos_valid = True
        fruit_rect = pygame.Rect(0, 0, FRUIT_RADIUS * 2, FRUIT_RADIUS * 2);
        fruit_rect.center = (fx, fy)
        for obs in obstacle_sprites_for_fruits:
            if fruit_rect.colliderect(obs.rect): original_pos_valid = False; break
        if original_pos_valid:
            if not (FRUIT_RADIUS <= fruit_rect.centerx <= SCREEN_WIDTH - FRUIT_RADIUS and \
                    FRUIT_RADIUS <= fruit_rect.centery <= SCREEN_HEIGHT - FRUIT_RADIUS): original_pos_valid = False
        if original_pos_valid:
            fruit_sprites.add(Fruit(fx, fy, ftype))
        else:
            print(f"Warning: Predefined fruit spawn for '{ftype}' at ({fx},{fy}) is invalid. Skipping.")

    game_state = STATE_PLAYING

# --- Save/Load Functions ---
def save_game_state(): # MODIFIED to handle saving from pause
    global current_level_index, game_state, player1, player2, boss_enemy, effect_manager, throwable_objects_group, state_before_pause

    actual_game_state_to_save = game_state
    if game_state == STATE_PAUSED:
        actual_game_state_to_save = state_before_pause # Use the state before pausing

    if actual_game_state_to_save != STATE_PLAYING and actual_game_state_to_save != STATE_BOSS_LEVEL:
        print("只能在遊玩關卡或Boss戰時存檔。")
        if game_state == STATE_PAUSED:
            print("(嘗試從暫停選單儲存，但先前狀態不允許儲存)")
        return

    save_data = {
        "current_level_index": current_level_index,
        "game_state_on_save": actual_game_state_to_save, # Save the actual gameplay state
        "player1": {
            "pos_x": player1.pos.x,
            "pos_y": player1.pos.y,
            "is_alive": player1.is_alive,
            "facing_left": player1.facing_left,
            "death_pos_x": player1.death_pos.x if player1.death_pos else None,
            "death_pos_y": player1.death_pos.y if player1.death_pos else None,
            "held_object_info": None
        },
        "player2": {
            "pos_x": player2.pos.x,
            "pos_y": player2.pos.y,
            "is_alive": player2.is_alive,
            "facing_left": player2.facing_left,
            "death_pos_x": player2.death_pos.x if player2.death_pos else None,
            "death_pos_y": player2.death_pos.y if player2.death_pos else None,
            "can_spawn_item_timer": player2.can_spawn_item_timer
        },
        "effect_manager": {
            "effects": {},
        },
        "boss_level_data": None,
        "throwable_objects": [],
        "coop_boxes": [],
        "fruits": [],
        "game_time_elapsed": game_time_elapsed, # Save game time
        "current_score": current_score,# Save current score
        "final_player_score": final_player_score,
    }

    for key, effect_data_val in effect_manager.effects.items():
        save_data["effect_manager"]["effects"][key] = {
            "active": effect_data_val["active"],
            "timer": effect_data_val["timer"]
        }
        if "flash_timer" in effect_data_val:
            save_data["effect_manager"]["effects"][key]["flash_timer"] = effect_data_val["flash_timer"]
        if "current_alpha" in effect_data_val:
            save_data["effect_manager"]["effects"][key]["current_alpha"] = effect_data_val["current_alpha"]
        if "meteor_timer" in effect_data_val:
            save_data["effect_manager"]["effects"][key]["meteor_timer"] = effect_data_val["meteor_timer"]

    if actual_game_state_to_save == STATE_BOSS_LEVEL:
        if boss_enemy:
            save_data["boss_level_data"] = {
                "boss_current_health": boss_enemy.current_health,
                "boss_pos_x": boss_enemy.pos.x,
                "boss_pos_y": boss_enemy.pos.y,
                "boss_movement_mode": boss_enemy.movement_mode,
                "boss_move_timer": boss_enemy.move_timer,
                "boss_current_direction_x": boss_enemy.current_direction.x,
                "boss_current_direction_y": boss_enemy.current_direction.y,
                "boss_teleport_timer": boss_enemy.teleport_timer,
                "boss_is_teleporting_warning": boss_enemy.is_teleporting_warning,
                "boss_teleport_target_pos_x": boss_enemy.teleport_target_pos.x if boss_enemy.teleport_target_pos else None,
                "boss_teleport_target_pos_y": boss_enemy.teleport_target_pos.y if boss_enemy.teleport_target_pos else None,
                "boss_attack_timer": boss_enemy.attack_timer,
            }

        player1_held_object_temp_id = -1
        if player1.held_object:
            player1_held_object_temp_id = id(player1.held_object)

        for i, obj in enumerate(throwable_objects_group):
            obj_data = {
                "temp_id": id(obj),
                "pos_x": obj.pos.x,
                "pos_y": obj.pos.y,
                "is_thrown": obj.is_thrown,
                "throw_velocity_x": obj.throw_velocity.x,
                "throw_velocity_y": obj.throw_velocity.y,
                "spawned_by_player_id": getattr(obj, "held_by_player_id", None),
                "is_held_by_p1": (id(obj) == player1_held_object_temp_id)
            }
            save_data["throwable_objects"].append(obj_data)
            if id(obj) == player1_held_object_temp_id:
                save_data["player1"]["held_object_info"] = obj_data

    elif actual_game_state_to_save == STATE_PLAYING:
        for box in coop_box_group:
            save_data["coop_boxes"].append({
                "pos_x": box.pos.x,
                "pos_y": box.pos.y
            })
            # 儲存所有水果的狀態
        fruits_data = []
        for fruit in fruit_sprites:
            fruits_data.append({
                "pos_x": fruit.rect.centerx,
                "pos_y": fruit.rect.centery,
                "fruit_type": fruit.fruit_type,
            })
        save_data["fruits"] = fruits_data


    try:
        with open(SAVE_FILE, 'w') as f:
            json.dump(save_data, f, indent=4)
        print(f"遊戲狀態已儲存至 {SAVE_FILE}")
    except Exception as e:
        print(f"儲存遊戲狀態時發生錯誤: {e}")

def load_game_state_from_file():
    global current_level_index, game_state, player1, player2, boss_enemy, effect_manager
    global laser_wall_sprites, goal_sprites, coop_box_group, spike_trap_group, fruit_sprites
    global meteor_sprites, warning_sprites, boss_group, throwable_objects_group, player_sprites
    global game_time_elapsed, current_score, final_player_score# Add game_time_elapsed, current_score

    try:
        with open(SAVE_FILE, 'r') as f:
            load_data = json.load(f)
        print(f"從 {SAVE_FILE} 載入遊戲狀態...")
    except FileNotFoundError:
        print(f"存檔 {SAVE_FILE} 未找到。開始新遊戲。")
        current_level_index = 0
        game_time_elapsed = 0.0
        current_score = 0
        load_level(current_level_index)
        return
    except Exception as e:
        print(f"載入遊戲狀態時發生錯誤: {e}。開始新遊戲。")
        current_level_index = 0
        game_time_elapsed = 0.0
        current_score = 0
        load_level(current_level_index)
        return

    laser_wall_sprites.empty()
    goal_sprites.empty()
    coop_box_group.empty()
    spike_trap_group.empty()
    fruit_sprites.empty()
    meteor_sprites.empty()
    warning_sprites.empty()
    boss_group.empty()
    throwable_objects_group.empty()
    if boss_enemy and hasattr(boss_enemy, 'projectiles'):
        boss_enemy.projectiles.empty()

    current_level_index = load_data.get("current_level_index", 0)
    saved_game_state_type = load_data.get("game_state_on_save", STATE_PLAYING)
    game_time_elapsed = load_data.get("game_time_elapsed", 0.0) # Load game time
    current_score = load_data.get("current_score", 0) # Load score
    final_player_score = load_data.get("final_player_score", 0)

    effect_manager.reset_all_effects()
    loaded_effects_manager_data = load_data.get("effect_manager", {}).get("effects", {})
    for key, effect_save_data in loaded_effects_manager_data.items():
        if key in effect_manager.effects:
            effect_manager.effects[key]["active"] = effect_save_data.get("active", False)
            effect_manager.effects[key]["timer"] = effect_save_data.get("timer", 0)
            if "flash_timer" in effect_manager.effects[key] and "flash_timer" in effect_save_data:
                effect_manager.effects[key]["flash_timer"] = effect_save_data["flash_timer"]
            if "current_alpha" in effect_manager.effects[key] and "current_alpha" in effect_save_data:
                effect_manager.effects[key]["current_alpha"] = effect_save_data["current_alpha"]
            elif key == "invisible_wall":
                effect_manager.effects[key]["current_alpha"] = effect_manager.default_laser_wall_alpha

            if "meteor_timer" in effect_manager.effects[key] and "meteor_timer" in effect_save_data:
                effect_manager.effects[key]["meteor_timer"] = effect_save_data["meteor_timer"]

    # Critical: Load the level *structure* first, then overwrite dynamic elements.
    # Temporarily set game_state to ensure load_level/setup_boss_level works as intended.
    original_game_state = game_state # Store current UI state
    game_state = saved_game_state_type # Pretend we are in the loaded game state type for loading

    if saved_game_state_type == STATE_BOSS_LEVEL:
        # setup_boss_level already resets player positions and some game elements.
        # It also sets game_state to STATE_BOSS_LEVEL.
        setup_boss_level()
    else:
        if current_level_index >= len(levels_data):
            print("錯誤：存檔的關卡索引超出範圍。開始新遊戲。")
            current_level_index = 0
            game_time_elapsed = 0.0
            current_score = 0
            load_level(current_level_index)
            game_state = original_game_state # Restore UI state if error
            return
        # load_level resets player positions, timer, score, and sets game_state to STATE_PLAYING.
        load_level(current_level_index)
        # After load_level, game_time_elapsed and current_score are reset, so restore them from save.
        game_time_elapsed = load_data.get("game_time_elapsed", 0.0)
        current_score = load_data.get("current_score", 0)


        coop_box_group.empty() # load_level populates this, so clear before loading saved positions
        loaded_coop_boxes = load_data.get("coop_boxes", [])
        for box_data in loaded_coop_boxes:
            coop_box_group.add(CoopBox(box_data["pos_x"], box_data["pos_y"], img=box_img))

        fruit_sprites.empty()
        loaded_fruits = load_data.get("fruits", [])
        for fruit_data in loaded_fruits:
            # 根據你的 Fruit 類別建構子調整以下一行
            fruit_sprites.add(Fruit(fruit_data["pos_x"], fruit_data["pos_y"], fruit_data["fruit_type"]))

    # Now, game_state reflects the loaded gameplay state (PLAYING or BOSS_LEVEL).
    # Restore player specifics
    player1.reset() # player.reset() is called in load_level/setup_boss_level, but good to be explicit
    p1_data = load_data.get("player1", {})
    player1.pos = pygame.math.Vector2(p1_data.get("pos_x", player1.start_pos.x),
                                      p1_data.get("pos_y", player1.start_pos.y))
    player1.is_alive = p1_data.get("is_alive", True)
    player1.facing_left = p1_data.get("facing_left", False)
    if not player1.is_alive:
        dp_x = p1_data.get("death_pos_x")
        dp_y = p1_data.get("death_pos_y")
        if dp_x is not None and dp_y is not None:
            player1.death_pos = pygame.math.Vector2(dp_x, dp_y)
            player1.original_death_pos_for_shake = pygame.math.Vector2(dp_x, dp_y)
            player1.rect.center = player1.death_pos
            player1._update_dead_image(0)
        else:
            player1.is_alive = True # Fallback if no death_pos
    else:
        player1.death_pos = None
    player1.rect.center = player1.pos

    player2.reset()
    p2_data = load_data.get("player2", {})
    player2.pos = pygame.math.Vector2(p2_data.get("pos_x", player2.start_pos.x),
                                      p2_data.get("pos_y", player2.start_pos.y))
    player2.is_alive = p2_data.get("is_alive", True)
    player2.facing_left = p2_data.get("facing_left", False)
    if not player2.is_alive:
        dp_x = p2_data.get("death_pos_x")
        dp_y = p2_data.get("death_pos_y")
        if dp_x is not None and dp_y is not None:
            player2.death_pos = pygame.math.Vector2(dp_x, dp_y)
            player2.original_death_pos_for_shake = pygame.math.Vector2(dp_x, dp_y)
            player2.rect.center = player2.death_pos
            player2._update_dead_image(0)
        else:
            player2.is_alive = True # Fallback
    else:
        player2.death_pos = None
    player2.rect.center = player2.pos
    player2.can_spawn_item_timer = p2_data.get("can_spawn_item_timer", 0)

    if saved_game_state_type == STATE_BOSS_LEVEL:
        boss_data = load_data.get("boss_level_data")
        if boss_data and boss_enemy: # boss_enemy should be re-initialized by setup_boss_level
            boss_enemy.current_health = boss_data.get("boss_current_health", boss_enemy.max_health)
            if boss_enemy.current_health <= 0:
                # This state should ideally not be saved, but handle it.
                game_state = STATE_BOSS_DEFEATED # The game state will be set to this after load
                boss_group.empty()
            else:
                boss_enemy.pos = pygame.math.Vector2(boss_data.get("boss_pos_x", SCREEN_WIDTH // 2),
                                                     boss_data.get("boss_pos_y", SCREEN_HEIGHT // 4))
                boss_enemy.rect.center = boss_enemy.pos
                boss_enemy.movement_mode = boss_data.get("boss_movement_mode", "simple_four_way")
                boss_enemy.move_timer = boss_data.get("boss_move_timer", 0)
                boss_enemy.current_direction = pygame.math.Vector2(boss_data.get("boss_current_direction_x", 0),
                                                                   boss_data.get("boss_current_direction_y", 0))
                boss_enemy.teleport_timer = boss_data.get("boss_teleport_timer", 0)
                boss_enemy.is_teleporting_warning = boss_data.get("boss_is_teleporting_warning", False)
                b_tp_x = boss_data.get("boss_teleport_target_pos_x")
                b_tp_y = boss_data.get("boss_teleport_target_pos_y")
                boss_enemy.teleport_target_pos = pygame.math.Vector2(b_tp_x,
                                                                     b_tp_y) if b_tp_x is not None and b_tp_y is not None else None
                boss_enemy.attack_timer = boss_data.get("boss_attack_timer", 0)
                if boss_enemy not in boss_group: boss_group.add(boss_enemy) # Ensure it's added back

        throwable_objects_group.empty() # Clear before loading saved ones
        player1.held_object = None

        loaded_throwables_data = load_data.get("throwable_objects", [])
        p1_held_object_data_from_save = p1_data.get("held_object_info")

        for obj_data in loaded_throwables_data:
            new_obj = ThrowableObject(obj_data["pos_x"], obj_data["pos_y"], obj_data.get("spawned_by_player_id", 1)) #
            new_obj.is_thrown = obj_data.get("is_thrown", False)
            new_obj.throw_velocity = pygame.math.Vector2(obj_data.get("throw_velocity_x", 0),
                                                         obj_data.get("throw_velocity_y", 0))
            throwable_objects_group.add(new_obj)

            if p1_held_object_data_from_save and \
                    obj_data.get("pos_x") == p1_held_object_data_from_save.get("pos_x") and \
                    obj_data.get("pos_y") == p1_held_object_data_from_save.get("pos_y") and \
                    obj_data.get("spawned_by_player_id") == p1_held_object_data_from_save.get(
                "spawned_by_player_id") and \
                    obj_data.get("is_held_by_p1", False):
                player1.held_object = new_obj
                new_obj.pickup(player1.player_id)

    player_sprites.empty() # Should be empty from load_level/setup_boss_level but ensure
    player_sprites.add(player1, player2)

    game_state = saved_game_state_type # Ensure game_state is finally set to the loaded gameplay state
    print("遊戲狀態已載入。")

def draw_leaderboard_screen(): # MODIFIED
    global leaderboard_menu_selected_index # Ensure access to the global
    screen.fill((20, 20, 40))
    title_text = font_large.render("排行榜", True, TEXT_COLOR)
    screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 10))

    if not leaderboard_data:
        no_data_text = font_small.render("尚無紀錄", True, TEXT_COLOR)
        screen.blit(no_data_text, (SCREEN_WIDTH // 2 - no_data_text.get_width() // 2, SCREEN_HEIGHT // 2))
    else:
        start_y = 150
        line_height = LEADERBOARD_FACE_SIZE[1] + 20
        header_y_offset = -40

        rank_x = 40
        face_p1_x = rank_x + 60
        face_p2_x = face_p1_x + LEADERBOARD_FACE_SIZE[0] + 10 # Gap between faces
        name_x = face_p2_x + LEADERBOARD_FACE_SIZE[0] + 25

        score_col_width = font_small.render("99/99", True, WHITE).get_width() + 10
        time_col_width = font_small.render("99:99.99", True, WHITE).get_width() + 20

        score_x = SCREEN_WIDTH - 70 - score_col_width // 2
        time_x = score_x - 30 - time_col_width // 2
        max_name_width = time_x - (name_x + font_small.render("...", True, WHITE).get_width()) - 20

        headers_info = [
            ("排名", rank_x + font_tiny.render("排名", True, WHITE).get_width() // 2),
            ("P1", face_p1_x + LEADERBOARD_FACE_SIZE[0] // 2),
            ("P2", face_p2_x + LEADERBOARD_FACE_SIZE[0] // 2),
            ("隊名/玩家名", name_x + max_name_width // 2),
            ("時間", time_x),
            ("分數", score_x)
        ]
        for header_text, hx_center in headers_info:
            header_surf = font_tiny.render(header_text, True, WHITE)
            screen.blit(header_surf, (hx_center - header_surf.get_width() // 2, start_y + header_y_offset))

        for i, entry in enumerate(leaderboard_data):
            if i >= MAX_LEADERBOARD_ENTRIES: break

            current_entry_y = start_y + i * line_height
            y_pos_center_of_row = current_entry_y + LEADERBOARD_FACE_SIZE[1] // 2

            rank_text_surf = font_small.render(f"{i + 1}.", True, TEXT_COLOR)
            screen.blit(rank_text_surf, (rank_x, y_pos_center_of_row - rank_text_surf.get_height() // 2))

            # Display P1 Face
            img_path_from_json_p1 = entry.get("face_image_path_p1")
            face_img_surface_p1 = None
            if img_path_from_json_p1:
                if img_path_from_json_p1 in loaded_face_images_cache:
                    face_img_surface_p1 = loaded_face_images_cache[img_path_from_json_p1]
                else:
                    absolute_image_path_p1 = os.path.normpath(os.path.join(SCRIPT_DIR, img_path_from_json_p1))
                    if os.path.exists(absolute_image_path_p1):
                        try:
                            raw_surface = pygame.image.load(absolute_image_path_p1).convert_alpha()
                            face_img_surface_p1 = pygame.transform.scale(raw_surface, LEADERBOARD_FACE_SIZE)
                            loaded_face_images_cache[img_path_from_json_p1] = face_img_surface_p1
                        except pygame.error as e:
                            print(f"排行榜載入 P1 影像錯誤 {absolute_image_path_p1}: {e}")
                            face_img_surface_p1 = None
            if face_img_surface_p1 is None:
                if default_face_image_surface:
                    face_img_surface_p1 = default_face_image_surface
                else:
                    face_img_surface_p1 = pygame.Surface(LEADERBOARD_FACE_SIZE, pygame.SRCALPHA)
                    face_img_surface_p1.fill((60, 60, 70, 180))
                    pygame.draw.rect(face_img_surface_p1, (100, 100, 110), (0, 0, *LEADERBOARD_FACE_SIZE), 1)

            screen.blit(face_img_surface_p1, (face_p1_x, current_entry_y))

            # Display P2 Face
            img_path_from_json_p2 = entry.get("face_image_path_p2")
            face_img_surface_p2 = None
            if img_path_from_json_p2:
                if img_path_from_json_p2 in loaded_face_images_cache:
                    face_img_surface_p2 = loaded_face_images_cache[img_path_from_json_p2]
                else:
                    absolute_image_path_p2 = os.path.normpath(os.path.join(SCRIPT_DIR, img_path_from_json_p2))
                    if os.path.exists(absolute_image_path_p2):
                        try:
                            raw_surface = pygame.image.load(absolute_image_path_p2).convert_alpha()
                            face_img_surface_p2 = pygame.transform.scale(raw_surface, LEADERBOARD_FACE_SIZE)
                            loaded_face_images_cache[img_path_from_json_p2] = face_img_surface_p2
                        except pygame.error as e:
                            print(f"排行榜載入 P2 影像錯誤 {absolute_image_path_p2}: {e}")
                            face_img_surface_p2 = None
            if face_img_surface_p2 is None:
                if default_face_image_surface:
                    face_img_surface_p2 = default_face_image_surface
                else:
                    face_img_surface_p2 = pygame.Surface(LEADERBOARD_FACE_SIZE, pygame.SRCALPHA)
                    face_img_surface_p2.fill((60, 60, 70, 180))
                    pygame.draw.rect(face_img_surface_p2, (100, 100, 110), (0, 0, *LEADERBOARD_FACE_SIZE), 1)

            screen.blit(face_img_surface_p2, (face_p2_x, current_entry_y))

            name_str_original = entry.get("name", "N/A") # Team/Entry Name
            name_text_surf = font_small.render(name_str_original, True, TEXT_COLOR)
            if name_text_surf.get_width() > max_name_width:
                temp_name = ""
                for char_idx in range(len(name_str_original)):
                    temp_name_check = name_str_original[:char_idx + 1] + "..."
                    if font_small.render(temp_name_check, True, TEXT_COLOR).get_width() > max_name_width:
                        name_str_display = name_str_original[:char_idx] + "..."
                        break
                else:
                    name_str_display = name_str_original
                name_text_surf = font_small.render(name_str_display, True, TEXT_COLOR)
            screen.blit(name_text_surf, (name_x, y_pos_center_of_row - name_text_surf.get_height() // 2))

            time_val = entry.get("time", float('inf'))
            time_str_display = "N/A"
            if time_val != float('inf'):
                minutes = int(time_val // 60)
                seconds = int(time_val % 60)
                milliseconds = int((time_val * 100) % 100)
                time_str_display = f"{minutes:02}:{seconds:02}.{milliseconds:02}"
            time_text_surf = font_small.render(time_str_display, True, TEXT_COLOR)
            screen.blit(time_text_surf, (time_x - time_text_surf.get_width() // 2,
                                         y_pos_center_of_row - time_text_surf.get_height() // 2))

            score_str_display = str(entry.get("score", "0"))
            score_text_surf = font_small.render(score_str_display, True, TEXT_COLOR)
            screen.blit(score_text_surf, (score_x - score_text_surf.get_width() // 2,
                                          y_pos_center_of_row - score_text_surf.get_height() // 2))

    option_padding = 50
    total_options_width = 0
    rendered_option_surfaces = []

    for i, (text, action_id) in enumerate(leaderboard_menu_options):
        display_text = text
        color = MENU_SELECTED_OPTION_COLOR if i == leaderboard_menu_selected_index else MENU_OPTION_COLOR
        option_surf = font_small.render(display_text, True, color)
        rendered_option_surfaces.append(option_surf)
        total_options_width += option_surf.get_width()
        if i < len(leaderboard_menu_options) - 1:
            total_options_width += option_padding

    current_x_pos = (SCREEN_WIDTH - total_options_width) // 2
    options_y_pos = SCREEN_HEIGHT - 70

    for i, option_surf in enumerate(rendered_option_surfaces):
        screen.blit(option_surf, (current_x_pos, options_y_pos))
        current_x_pos += option_surf.get_width() + option_padding

def populate_level_select_options():
    global level_select_options
    level_select_options = []
    for i in range(len(levels_data)):
        level_select_options.append(f"關卡 {i + 1}")
    level_select_options.append("魔王關卡")
    level_select_options.append("返回主選單")

# Load the background image for the level select menu
level_select_background = pygame.image.load(os.path.join('plays_animation_art', 'Background_menu.png')).convert()
level_select_background = pygame.transform.scale(level_select_background, (SCREEN_WIDTH, SCREEN_HEIGHT))

def draw_level_select_menu():
    screen.blit(level_select_background, (0, 0))  # Draw the background image
    title_text = font_large.render("選擇關卡", True, TEXT_COLOR)
    screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 50))

    for i, option_text in enumerate(level_select_options):
        color = MENU_SELECTED_OPTION_COLOR if i == level_select_selected_index else MENU_OPTION_COLOR
        text_surf = font_menu.render(option_text, True, color)
        text_rect = text_surf.get_rect(center=(SCREEN_WIDTH // 2, 200 + i * 60))
        screen.blit(text_surf, text_rect)

def draw_pause_menu():
    # Draw a semi-transparent overlay
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill(PAUSE_OVERLAY_COLOR)
    screen.blit(overlay, (0, 0))

    title_text = font_large.render("遊戲暫停", True, TEXT_COLOR)
    screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 100))

    for i, option_text in enumerate(pause_menu_options):
        color = MENU_SELECTED_OPTION_COLOR if i == pause_menu_selected_index else MENU_OPTION_COLOR
        text_surf = font_menu.render(option_text, True, color)
        text_rect = text_surf.get_rect(center=(SCREEN_WIDTH // 2, 250 + i * 70))
        screen.blit(text_surf, text_rect)

game_state = STATE_START_SCREEN
last_game_state = None
running = True

# --- 音樂初始化 ---
pygame.mixer.init() #
start_screen_music_played = False

prompt_text_visible = True

# ---復活設置---
REVIVE_HOLD_TIME = 1.5 #
revive_progress = 0.0 #
revive_target = None #

# Start the drawing window in a separate thread
start_drawing_thread()

# Load the background image for the main menu
default_menu_background = pygame.image.load(os.path.join('plays_animation_art', 'Background_menu.png')).convert()
default_menu_background = pygame.transform.scale(default_menu_background, (SCREEN_WIDTH, SCREEN_HEIGHT))

def draw_game_state_messages():
    global game_time_elapsed, current_score

    if game_state == STATE_PLAYING and current_level_index == 0:
        tutorial_text1 = font_tiny.render("移動：玩家1用WASD移動，玩家2用方向鍵移動", True, (255, 255, 0))
        tutorial_text2 = font_tiny.render("過關目標：兩人都走到各自顏色的終點", True, (255, 255, 0))
        screen.blit(tutorial_text1, (SCREEN_WIDTH // 2 - tutorial_text1.get_width() // 2, 40))
        screen.blit(tutorial_text2, (SCREEN_WIDTH // 2 - tutorial_text2.get_width() // 2, 80))
        tutorial_text3 = font_tiny.render("箱子: 需兩人一起才能被推動", True, (255, 255, 255))
        screen.blit(tutorial_text3, (SCREEN_WIDTH // 2 - tutorial_text3.get_width() // 2 - 250, 130))
        tutorial_text4 = font_tiny.render("地刺:縮回時可通過，伸出時碰觸會死亡", True, (255, 255, 255))
        screen.blit(tutorial_text4, (SCREEN_WIDTH // 2 - tutorial_text4.get_width() // 2 - 250, SCREEN_HEIGHT - 250))
        tutorial_text5 = font_tiny.render("藍色:牆壁隱形，灰色:操控方向相反", True, (255, 255, 255))
        screen.blit(tutorial_text5, (SCREEN_WIDTH // 2 - tutorial_text5.get_width() // 2 + 220, SCREEN_HEIGHT - 280))
        tutorial_text6 = font_tiny.render("紅色:會召喚隕石墜落", True, (255, 255, 255))
        screen.blit(tutorial_text6, (SCREEN_WIDTH // 2 - tutorial_text5.get_width() // 2 + 220, SCREEN_HEIGHT - 310))
        tutorial_text7 = font_tiny.render("雷射牆壁:碰觸到會死亡", True, (255, 255, 255))
        screen.blit(tutorial_text7, (SCREEN_WIDTH // 2 - tutorial_text5.get_width() // 2 + 220, 140))

    if game_state == STATE_GAME_OVER:
        game_over_text = font_large.render("遊戲結束", True, TEXT_COLOR)
        restart_text = font_small.render("按 R 鍵重新開始", True, TEXT_COLOR)
        screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, SCREEN_HEIGHT // 2 - 60))
        screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 30))
    elif game_state == STATE_BOSS_DEFEATED:
        victory_text = font_large.render("Boss 已擊敗！恭喜！", True, (0, 255, 0))
        screen.blit(victory_text, (SCREEN_WIDTH // 2 - victory_text.get_width() // 2, 10))
        # 顯示提示
        if boss_defeated_area_rect:
            prompt_text = font_small.render("兩位玩家請一起走到綠色區域", True, (0, 255, 0))
            screen.blit(prompt_text, (SCREEN_WIDTH // 2 - prompt_text.get_width() // 2, 100))

    if game_state == STATE_PLAYING:
        level_text = font_small.render(f"關卡 {current_level_index + 1}", True, TEXT_COLOR) #
        screen.blit(level_text, (10, 10))

        timer_val_str = f"{int(game_time_elapsed // 60):02}:{int(game_time_elapsed % 60):02}" # 格式化為 MM:SS
        timer_text_surf = font_tiny.render(f"時間: {timer_val_str}", True, TEXT_COLOR)
        screen.blit(timer_text_surf, (SCREEN_WIDTH - timer_text_surf.get_width() - 10, 10))

        score_text_surf = font_tiny.render(f"分數: {current_score}/{MAX_TOTAL_SCORE}", True, TEXT_COLOR) #
        screen.blit(score_text_surf, (SCREEN_WIDTH - score_text_surf.get_width() - 10, 35))

        p1_status_text = "存活" if player1.is_alive else "死亡";
        p2_status_text = "存活" if player2.is_alive else "死亡"
        p1_text = font_tiny.render(f"玩家1: {p1_status_text}", True, PLAYER1_COLOR);
        screen.blit(p1_text, (10, 50))
        p2_text = font_tiny.render(f"玩家2: {p2_status_text}", True, PLAYER2_COLOR);
        screen.blit(p2_text, (10, 75))
        if (player1.is_alive and not player2.is_alive) or (player2.is_alive and not player1.is_alive):
            revive_hint = font_tiny.render("請 P1 按住'F' / P2 按住'.' 幫隊友復活", True, REVIVE_PROMPT_COLOR) #
            screen.blit(revive_hint, (SCREEN_WIDTH // 2 - revive_hint.get_width() // 2, 10))
        active_effects = effect_manager.get_active_effects_info() #
        y_offset = 100
        for effect_str in active_effects:
            effect_surf = font_effect.render(effect_str, True, TEXT_COLOR);
            screen.blit(effect_surf, (10, y_offset));
            y_offset += 20
        if player1.is_alive and player2.is_alive and coop_box_group:
            first_box = next(iter(coop_box_group));
            p1_near = player1.pos.distance_to(first_box.pos) < COOP_BOX_PUSH_RADIUS
            p2_near = player2.pos.distance_to(first_box.pos) < COOP_BOX_PUSH_RADIUS #
            if p1_near and p2_near: #
                push_hint = font_tiny.render("兩人靠近可推箱", True, (225, 210, 80));
                screen.blit(push_hint, (SCREEN_WIDTH // 2 - push_hint.get_width() // 2, 40))
    elif game_state == STATE_BOSS_LEVEL:
        boss_level_text = font_large.render("!! BOSS BATTLE !!", True, (255, 50, 50))
        screen.blit(boss_level_text, (SCREEN_WIDTH // 2 - boss_level_text.get_width() // 2, 10))

        timer_val_str = f"{int(game_time_elapsed // 60):02}:{int(game_time_elapsed % 60):02}"
        timer_text_surf = font_tiny.render(f"時間: {timer_val_str}", True, TEXT_COLOR)
        screen.blit(timer_text_surf, (SCREEN_WIDTH - timer_text_surf.get_width() - 10, 60))

        p1_status_text = "存活" if player1.is_alive else "死亡";
        p2_status_text = "存活" if player2.is_alive else "死亡"
        p1_text = font_tiny.render(f"玩家1: {p1_status_text}", True, PLAYER1_COLOR);
        screen.blit(p1_text, (10, SCREEN_HEIGHT - 80))
        p2_text = font_tiny.render(f"玩家2: {p2_status_text}", True, PLAYER2_COLOR);
        screen.blit(p2_text, (10, SCREEN_HEIGHT - 55))
        if (player1.is_alive and not player2.is_alive) or (player2.is_alive and not player1.is_alive):
            revive_hint = font_tiny.render("請 P1 按住'F' / P2 按住'.' 幫隊友復活", True, REVIVE_PROMPT_COLOR)
            screen.blit(revive_hint, (SCREEN_WIDTH // 2 - revive_hint.get_width() // 2, SCREEN_HEIGHT - 30))

        if player2.is_alive and player2.can_spawn_item_timer > 0:
            cd_text = font_effect.render(f"P2 物品CD: {player2.can_spawn_item_timer:.1f}s", True, WHITE)
            screen.blit(cd_text, (SCREEN_WIDTH - cd_text.get_width() - 10, 10))
        elif player2.is_alive:
            cd_text = font_effect.render(f"P2 按 ; 可造物", True, (100, 255, 100))
            screen.blit(cd_text, (SCREEN_WIDTH - cd_text.get_width() - 10, 10))

        if player1.is_alive:
            action_hint_text = "按 G 拾取"
            if player1.held_object:
                action_hint_text = "按 G 投擲"
            p1_action_hint = font_effect.render(action_hint_text, True, WHITE)
            screen.blit(p1_action_hint, (10, SCREEN_HEIGHT - 100))

populate_level_select_options() # NEW: Initialize level select options

# ---遊戲主程式循環---
final_battle_music_started = False
while running: #
    dt = clock.tick(FPS) / 1000.0 #
    keys = pygame.key.get_pressed() #

    if show_save_feedback:
        save_feedback_timer -= dt
        if save_feedback_timer <= 0:
            show_save_feedback = False

    for event in pygame.event.get(): #
        if event.type == pygame.QUIT:
            running = False #
        elif event.type == pygame.USEREVENT + 1: # USEREVENT 應該是 elif，以避免同時是QUIT又是USEREVENT的罕見情況
            if boss_enemy: boss_enemy.revert_color() #

        elif event.type == pygame.KEYDOWN: #
            # --- 全域熱鍵 ---
            if event.key == pygame.K_F5: #
                save_game_state() # save_game_state will handle context #
            elif event.key == pygame.K_F9: #
                pygame.mixer.music.stop() #
                load_game_state_from_file() #
                if game_state != STATE_PAUSED:
                    pass
                else:
                    pygame.mixer.music.pause()

            # --- STATE_START_SCREEN ---
            if game_state == STATE_START_SCREEN: # # 從 elif 改為 if (或保持 elif 如果 F5/F9 之後不應有其他操作)
                if event.key == pygame.K_UP: #
                    start_menu_selected_index = (start_menu_selected_index - 1) % len(start_menu_options) #
                elif event.key == pygame.K_DOWN: #
                    start_menu_selected_index = (start_menu_selected_index + 1) % len(start_menu_options) #
                elif event.key == pygame.K_RETURN: #
                    selected_option_text = start_menu_options[start_menu_selected_index] #

                    if selected_option_text == "開始新遊戲": #
                        current_level_index = 0 #
                        load_level(current_level_index) #
                    elif selected_option_text == "選擇關卡": #
                        level_select_selected_index = 0 # Reset selection for level select screen #
                        game_state = STATE_LEVEL_SELECT #
                    elif selected_option_text == "載入遊戲": #
                        pygame.mixer.music.stop()
                        load_game_state_from_file() #
                    elif selected_option_text == "查看排行榜": #
                        leaderboard_menu_selected_index = 0 #
                        load_leaderboard() #
                        game_state = STATE_SHOW_LEADERBOARD #
                    elif selected_option_text == "離開遊戲": #
                        running = False #
                elif event.key == pygame.K_q: #
                    if "離開遊戲" in start_menu_options[
                        start_menu_selected_index] or "離開遊戲" not in start_menu_options: #
                        running = False #

            # --- STATE_LEVEL_SELECT ---
            elif game_state == STATE_LEVEL_SELECT: # NEW: Event handling for level select #
                if event.key == pygame.K_UP: #
                    level_select_selected_index = (level_select_selected_index - 1) % len(level_select_options) #
                elif event.key == pygame.K_DOWN: #
                    level_select_selected_index = (level_select_selected_index + 1) % len(level_select_options) #
                elif event.key == pygame.K_RETURN: #
                    selected_option_text = level_select_options[level_select_selected_index] #
                    if selected_option_text == "返回主選單":
                        game_state = STATE_START_SCREEN #
                    elif selected_option_text == "魔王關卡": #
                        game_time_elapsed = 0.0 # Reset timer for boss if selected directly #
                        current_score = 0 # Reset score if boss selected directly #
                        setup_boss_level() #
                    else: # It's "關卡 X" #
                        level_num_str = selected_option_text.split(" ")[1] #
                        selected_level_idx = int(level_num_str) - 1 #
                        if 0 <= selected_level_idx < len(levels_data): #
                            current_level_index = selected_level_idx #
                            load_level(current_level_index) #
                        else: #
                            print(f"無效的選擇關卡索引: {selected_level_idx}") #
                            game_state = STATE_START_SCREEN # Fallback #
                elif event.key == pygame.K_ESCAPE or event.key == pygame.K_b: # Allow Esc or B to go back #
                    game_state = STATE_START_SCREEN #

            # --- STATE_PLAYING or STATE_BOSS_LEVEL ---
            elif game_state == STATE_PLAYING or game_state == STATE_BOSS_LEVEL: # MODIFIED to include ESC for pause #
                if event.key == pygame.K_ESCAPE: #
                    state_before_pause = game_state #
                    game_state = STATE_PAUSED #
                    pause_menu_selected_index = 0 # Reset selection #
                    pygame.mixer.music.pause() # Pause current music #
                # 如果不是 ESCAPE，且當前是 BOSS 關卡，則處理 BOSS 關卡的特定按鍵
                elif game_state == STATE_BOSS_LEVEL: # Boss specific actions # # 再次檢查 game_state 因為可能已被改成 PAUSED
                    if event.key == ACTION_KEY_P1: #
                        player1.handle_action_key(throwable_objects_group) #
                    elif event.key == DRAW_ITEM_KEY_P2: #
                        target_spawn_pos = player1.pos if player1.is_alive else pygame.math.Vector2(
                            ITEM_SPAWN_POS_DEFAULT) #
                        player2.handle_draw_item_key(throwable_objects_group, target_spawn_pos,get_shape_from_queue()) #

            # --- STATE_PAUSED ---
            elif game_state == STATE_PAUSED: # NEW: Event handling for pause menu #
                if event.key == pygame.K_UP: #dw
                    pause_menu_selected_index = (pause_menu_selected_index - 1) % len(pause_menu_options) #
                elif event.key == pygame.K_DOWN: #
                    pause_menu_selected_index = (pause_menu_selected_index + 1) % len(pause_menu_options) #
                elif event.key == pygame.K_RETURN: #
                    selected_action = pause_menu_options[pause_menu_selected_index] #
                    if "繼續遊戲" in selected_action: # Resume #
                        game_state = state_before_pause #
                        pygame.mixer.music.unpause() #
                    elif "重新開始關卡" in selected_action: # Restart Level #
                        pygame.mixer.music.unpause()
                        if state_before_pause == STATE_PLAYING: #
                            load_level(current_level_index) #
                        elif state_before_pause == STATE_BOSS_LEVEL: #
                            game_time_elapsed = 0.0 # Reset timer if restarting boss from pause #
                            setup_boss_level() #
                    elif "儲存遊戲" in selected_action: # Save Game #
                        save_game_state() #
                        show_save_feedback = True
                        save_feedback_timer = SAVE_FEEDBACK_DURATION
                    elif "載入遊戲" in selected_action: # Load Game #
                        pygame.mixer.music.stop()
                        load_game_state_from_file() #
                    elif "回到主選單" in selected_action: # Back to Main Menu #

                        final_player_score = 0
                        pygame.mixer.music.unpause()
                        game_state = STATE_START_SCREEN #
                    elif "離開遊戲" in selected_action: # Quit #
                        running = False #
                elif event.key == pygame.K_ESCAPE: # Allow ESC to also resume #
                    game_state = state_before_pause #
                    pygame.mixer.music.unpause() #

                elif event.key == pygame.K_r and "重新開始關卡 (R)" in pause_menu_options[pause_menu_selected_index]: #
                    pygame.mixer.music.unpause() #
                    if state_before_pause == STATE_PLAYING:
                        load_level(current_level_index) #
                    elif state_before_pause == STATE_BOSS_LEVEL:
                        setup_boss_level() #
                elif event.key == pygame.K_F5 and "儲存遊戲 (F5)" in pause_menu_options[pause_menu_selected_index]: #
                    save_game_state() #
                elif event.key == pygame.K_F9 and "載入遊戲 (F9)" in pause_menu_options[pause_menu_selected_index]: #
                    pygame.mixer.music.stop() #
                    load_game_state_from_file() #
                elif event.key == pygame.K_b and "回到主選單 (B)" in pause_menu_options[pause_menu_selected_index]: #
                    pygame.mixer.music.unpause() #
                    game_state = STATE_START_SCREEN #
                elif event.key == pygame.K_q and "離開遊戲 (Q)" in pause_menu_options[pause_menu_selected_index]: #
                    running = False #

            # --- STATE_GAME_OVER ---
            elif game_state == STATE_GAME_OVER: # Simpler game over, only R to restart all #
                if event.key == pygame.K_r: #
                    current_level_index = 0 #
                    final_player_score = 0
                    load_level(current_level_index) #

            # --- STATE_ASK_CAMERA ---
            elif game_state == STATE_ASK_CAMERA: #
                if event.key == pygame.K_y: #
                    game_state = STATE_CAMERA_INPUT #
                    player_name_input_active = True #
                    camera_capture_active = False #
                    post_capture_prompt_active = False #
                    current_player_name = "" #
                    captured_face_image_path_p1 = None #
                    captured_face_image_path_p2 = None #
                    current_capture_player_index = 0 # Start with P1 #
                    photo_taken_for_current_player_flag = False #
                elif event.key == pygame.K_n: #
                    add_leaderboard_entry("Anonymous", final_game_time, final_player_score, None,
                                          None) # Add with no photos #
                    save_leaderboard() #
                    leaderboard_menu_selected_index = 0 #
                    game_state = STATE_SHOW_LEADERBOARD #

            # --- STATE_CAMERA_INPUT ---
            elif game_state == STATE_CAMERA_INPUT:
                if player_name_input_active:
                    if event.key == pygame.K_RETURN:
                        if current_player_name.strip():
                            player_name_input_active = False
                            initialize_camera_for_capture()
                            current_capture_player_index = 0 # Start with P1 face #
                            post_capture_prompt_active = False
                            photo_taken_for_current_player_flag = False
                        else: #
                            print("提示：隊伍/玩家名稱不能為空白。")
                    elif event.key == pygame.K_BACKSPACE:
                            current_player_name = current_player_name[:-1]
                    elif event.unicode.isprintable():
                        if len(current_player_name) < 20:
                            current_player_name += event.unicode

                elif camera_capture_active and not post_capture_prompt_active: # Actively capturing for current_capture_player_index #
                    if event.key == pygame.K_a: # Capture for current player #
                        handle_photo_capture(current_capture_player_index) # This will set post_capture_prompt_active #
                        photo_taken_for_current_player_flag = True # Mark that an attempt was made #
                    elif event.key == pygame.K_s: # Skip current player's photo #
                        if current_capture_player_index == 0: #
                            captured_face_image_path_p1 = None #
                            print("玩家1 照片已略過。") #
                        else: #
                            captured_face_image_path_p2 = None #
                            print("玩家2 照片已略過。") #
                        photo_taken_for_current_player_flag = True #
                        post_capture_prompt_active = True # Go to prompt #
                    elif event.key == pygame.K_q: # Quit entire capture to leaderboard #
                        release_camera_resources() #
                        add_leaderboard_entry(current_player_name, final_game_time, final_player_score,
                                              captured_face_image_path_p1, captured_face_image_path_p2) #
                        save_leaderboard() #
                        leaderboard_menu_selected_index = 0 # Reset selection
                        game_state = STATE_SHOW_LEADERBOARD #

                elif post_capture_prompt_active: # After a capture/skip attempt for the current player #
                    if current_capture_player_index == 0: # P1's post-capture options #
                        if event.key == pygame.K_r: # Retry P1 #
                            post_capture_prompt_active = False #
                            photo_taken_for_current_player_flag = False #
                        elif event.key == pygame.K_n: # Next (to P2) #
                            current_capture_player_index = 1 #
                            post_capture_prompt_active = False #
                            photo_taken_for_current_player_flag = False #
                            if not cap or not cap.isOpened(): initialize_camera_for_capture() #
                        elif event.key == pygame.K_f: # Finish (save with P1 only, P2 skipped) #
                            add_leaderboard_entry(current_player_name, final_game_time, final_player_score,
                                                  captured_face_image_path_p1, None) #
                            save_leaderboard() #
                            release_camera_resources() #
                            leaderboard_menu_selected_index = 0 # Reset selection
                            game_state = STATE_SHOW_LEADERBOARD #

                    elif current_capture_player_index == 1: # P2's post-capture options #
                        if event.key == pygame.K_r: # Retry P2 #
                            post_capture_prompt_active = False #
                            photo_taken_for_current_player_flag = False #
                        elif event.key == pygame.K_b: # Back to P1's post-capture options #
                            current_capture_player_index = 0 #
                            post_capture_prompt_active = True # Stay in prompt mode, but for P1 #
                            photo_taken_for_current_player_flag = True # P1's previous status #
                        elif event.key == pygame.K_f: # Finish (save with P1 and P2 photos) #
                            add_leaderboard_entry(current_player_name, final_game_time, final_player_score,
                                                  captured_face_image_path_p1, captured_face_image_path_p2) #
                            save_leaderboard() #
                            release_camera_resources() #
                            leaderboard_menu_selected_index = 0 # Reset selection
                            game_state = STATE_SHOW_LEADERBOARD #

            # --- STATE_SHOW_LEADERBOARD ---
            # MODIFIED event handling for leaderboard menu
            elif game_state == STATE_SHOW_LEADERBOARD:
                if event.key == pygame.K_LEFT:
                    leaderboard_menu_selected_index = (leaderboard_menu_selected_index - 1) % len(leaderboard_menu_options)
                elif event.key == pygame.K_RIGHT:
                    leaderboard_menu_selected_index = (leaderboard_menu_selected_index + 1) % len(leaderboard_menu_options)
                elif event.key == pygame.K_RETURN:
                    selected_action_id = leaderboard_menu_options[leaderboard_menu_selected_index][1]

                    if selected_action_id == "RESTART":
                        current_level_index = 0
                        game_time_elapsed = 0.0
                        current_score = 0
                        # load_leaderboard() #
                        current_player_name = ""
                        captured_face_image_path_p1 = None
                        captured_face_image_path_p2 = None
                        player_name_input_active = False
                        camera_capture_active = False
                        post_capture_prompt_active = False
                        current_capture_player_index = 0
                        photo_taken_for_current_player_flag = False
                        load_level(current_level_index) # This will set game_state to STATE_PLAYING
                    elif selected_action_id == "MAIN_MENU":
                        game_state = STATE_START_SCREEN
                        start_menu_selected_index = 0 # Reset start menu selection
                    elif selected_action_id == "QUIT":
                        running = False
                elif event.key == pygame.K_ESCAPE: # Optional: ESC to go to main menu
                    game_state = STATE_START_SCREEN
                    start_menu_selected_index = 0


                    # Game logic updates (should not run if paused)
    if game_state == STATE_PLAYING:
        game_time_elapsed += dt
        effect_manager.update(dt)
        player1.update_movement(laser_wall_sprites, coop_box_group, spike_trap_group, meteor_sprites, effect_manager,
                                dt)
        player2.update_movement(laser_wall_sprites, coop_box_group, spike_trap_group, meteor_sprites, effect_manager,
                                dt)

        for player in player_sprites:
            if player.is_alive:
                collided_fruits = pygame.sprite.spritecollide(player, fruit_sprites, True)
                for fruit in collided_fruits:

                    if current_score < MAX_TOTAL_SCORE: #
                            current_score += SCORE_FRUIT_VALUE #

                    effect_manager.apply_effect(fruit.fruit_type, player.player_id)

        if effect_manager.should_spawn_meteor(): #
            spawn_x = random.randint(METEOR_SIZE, SCREEN_WIDTH - METEOR_SIZE);
            spawn_y = random.randint(METEOR_SIZE, SCREEN_HEIGHT - METEOR_SIZE) #
            warning_sprites.add(Warning(spawn_x, spawn_y, METEOR_WARNING_TIME));
            effect_manager.reset_meteor_timer() #
        for warning in list(warning_sprites): #
            if warning.update(dt): meteor_sprites.add(Meteor(warning.spawn_pos[0], warning.spawn_pos[1])) #
        warning_sprites.update(dt);
        meteor_sprites.update(dt) #

        if player1.is_alive and player2.is_alive: #
            for coop_box in coop_box_group: #
                p1_near = player1.pos.distance_to(coop_box.pos) < COOP_BOX_PUSH_RADIUS;
                p2_near = player2.pos.distance_to(coop_box.pos) < COOP_BOX_PUSH_RADIUS #
                if p1_near and p2_near: #
                    total_dir = pygame.math.Vector2(0, 0)
                    if keys[player1.control_keys['right']]: total_dir.x += 1; #
                    if keys[player1.control_keys['left']]: total_dir.x -= 1 #
                    if keys[player1.control_keys['down']]: total_dir.y += 1 #
                    if keys[player1.control_keys['up']]: total_dir.y -= 1 #
                    if keys[player2.control_keys['right']]: total_dir.x += 1 #
                    if keys[player2.control_keys['left']]: total_dir.x -= 1 #
                    if keys[player2.control_keys['down']]: total_dir.y += 1 #
                    if keys[player2.control_keys['up']]: total_dir.y -= 1 #
                    if total_dir.length_squared() > 0: total_dir.normalize_ip(); coop_box.move(total_dir,
                                                                                               laser_wall_sprites) #
        for _ in range(CHAIN_ITERATIONS): #
            if player1.is_alive and player2.is_alive:
                p1_pos_vec = player1.pos;
                p2_pos_vec = player2.pos;
                delta = p2_pos_vec - p1_pos_vec;
                distance = delta.length()
                if distance > CHAIN_MAX_LENGTH and distance != 0: #
                    diff = (distance - CHAIN_MAX_LENGTH) / distance; #
                    p1_new_pos = player1.pos + delta * 0.5 * diff;
                    p2_new_pos = player2.pos - delta * 0.5 * diff
                    player1.pos.x = max(player1.rect.width // 2,
                                        min(p1_new_pos.x, SCREEN_WIDTH - player1.rect.width // 2));
                    player1.pos.y = max(player1.rect.height // 2,
                                        min(p1_new_pos.y, SCREEN_HEIGHT - player1.rect.height // 2))
                    player2.pos.x = max(player2.rect.width // 2,
                                        min(p2_new_pos.x, SCREEN_WIDTH - player2.rect.width // 2));
                    player2.pos.y = max(player2.rect.height // 2,
                                        min(p2_new_pos.y, SCREEN_HEIGHT - player2.rect.height // 2))
                    player1.rect.center = player1.pos;
                    player2.rect.center = player2.pos
            elif player1.is_alive and not player2.is_alive and player2.death_pos:
                delta = player2.death_pos - player1.pos;
                distance = delta.length()
                if distance > CHAIN_MAX_LENGTH and distance != 0: #
                    diff_factor = (distance - CHAIN_MAX_LENGTH) / distance; #
                    p1_new_pos = player1.pos + delta * diff_factor
                    player1.pos.x = max(player1.rect.width // 2,
                                        min(p1_new_pos.x, SCREEN_WIDTH - player1.rect.width // 2));
                    player1.pos.y = max(player1.rect.height // 2,
                                        min(p1_new_pos.y, SCREEN_HEIGHT - player1.rect.height // 2));
                    player1.rect.center = player1.pos
            elif player2.is_alive and not player1.is_alive and player1.death_pos:
                delta = player1.death_pos - player2.pos;
                distance = delta.length()
                if distance > CHAIN_MAX_LENGTH and distance != 0: #
                    diff_factor = (distance - CHAIN_MAX_LENGTH) / distance; #
                    p2_new_pos = player2.pos + delta * diff_factor
                    player2.pos.x = max(player2.rect.width // 2,
                                        min(p2_new_pos.x, SCREEN_WIDTH - player2.rect.width // 2));
                    player2.pos.y = max(player2.rect.height // 2,
                                        min(p2_new_pos.y, SCREEN_HEIGHT - player2.rect.height // 2));
                    player2.rect.center = player2.pos
        #print(final_player_score)
        goal1.update_status(player1)
        goal2.update_status(player2) #
        if goal1.is_active and goal2.is_active and player1.is_alive and player2.is_alive: #
            current_level_index += 1 #
            # 關卡過關時累加分數
            final_player_score += current_score
            load_level(current_level_index) # This might change game_state to STATE_BOSS_LEVEL
        if not player1.is_alive and not player2.is_alive: game_state = STATE_GAME_OVER #

    elif game_state == STATE_BOSS_LEVEL:
        game_time_elapsed += dt
        #print(final_player_score)
        player1.update_movement(None, None, None, None, effect_manager, dt, boss_enemy, boss_enemy.projectiles,
                                throwable_objects_group)
        player2.update_movement(None, None, None, None, effect_manager, dt, boss_enemy, boss_enemy.projectiles,
                                throwable_objects_group)
        player1.update_boss_interactions(dt)
        player2.update_boss_interactions(dt)

        if boss_enemy:
            if boss_enemy.current_health > boss_enemy.max_health / 2: #
                if not boss_music_playing:
                    fade_out_and_switch_music(None, BOSS_MUSIC, fade_duration=0) #
                    boss_music_playing = True
                final_battle_music_started = False
            elif not final_battle_music_started and boss_enemy.current_health <= boss_enemy.max_health / 2: #
                fade_out_and_switch_music(BOSS_MUSIC, FINAL_BATTLE_MUSIC, fade_duration=2) #
                final_battle_music_started = True
                boss_music_playing = False

            boss_enemy.update(dt, player_sprites, SCREEN_WIDTH, SCREEN_HEIGHT)
            for obj in throwable_objects_group:
                if obj.is_thrown and boss_enemy.rect.colliderect(obj.rect):
                    boss_enemy.take_damage(obj.damage)
                    obj.kill()
                    if boss_enemy.current_health <= 0:
                        # Game state transition to ASK_CAMERA will be handled below
                        break
            if boss_enemy.current_health <= 0:
                final_game_time = game_time_elapsed
                 # Use current_score from regular levels as boss doesn't have separate scoring

                boss_group.empty()
                throwable_objects_group.empty()
                if boss_enemy and hasattr(boss_enemy, 'projectiles'): boss_enemy.projectiles.empty()

                pygame.mixer.music.stop()
                leaderboard_menu_selected_index = 0
                # 產生 Boss 被擊敗後的正方形區域
                boss_defeated_area_size = 120
                boss_defeated_area_rect = pygame.Rect(0, 0, boss_defeated_area_size, boss_defeated_area_size)
                boss_defeated_area_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
                # 進入 boss_defeated_area_rect 狀態時所有死亡的 player 都會復活
                if not player1.is_alive:
                    player1.is_alive = True
                    player1.revive() if hasattr(player1, 'revive') else None
                if not player2.is_alive:
                    player2.is_alive = True
                    player2.revive() if hasattr(player2, 'revive') else None
                game_state = STATE_BOSS_DEFEATED
            elif not player1.is_alive and not player2.is_alive:
                game_state = STATE_GAME_OVER

        throwable_objects_group.update(dt)
        if player1.held_object: player1.held_object.update(dt, player1.pos, player1.facing_left)

        for _ in range(CHAIN_ITERATIONS): # Chain logic for boss level
            if player1.is_alive and player2.is_alive:
                p1_pos_vec = player1.pos;
                p2_pos_vec = player2.pos;
                delta = p2_pos_vec - p1_pos_vec;
                distance = delta.length()
                if distance > CHAIN_MAX_LENGTH and distance != 0:
                    diff = (distance - CHAIN_MAX_LENGTH) / distance;
                    p1_new_pos = player1.pos + delta * 0.5 * diff;
                    p2_new_pos = player2.pos - delta * 0.5 * diff
                    player1.pos.x = max(player1.rect.width // 2,
                                        min(p1_new_pos.x, SCREEN_WIDTH - player1.rect.width // 2));
                    player1.pos.y = max(player1.rect.height // 2,
                                        min(p1_new_pos.y, SCREEN_HEIGHT - player1.rect.height // 2))
                    player2.pos.x = max(player2.rect.width // 2,
                                        min(p2_new_pos.x, SCREEN_WIDTH - player2.rect.width // 2));
                    player2.pos.y = max(player2.rect.height // 2,
                                        min(p2_new_pos.y, SCREEN_HEIGHT - player2.rect.height // 2))
                    player1.rect.center = player1.pos;
                    player2.rect.center = player2.pos
            elif player1.is_alive and not player2.is_alive and player2.death_pos:
                delta = player2.death_pos - player1.pos;
                distance = delta.length()
                if distance > CHAIN_MAX_LENGTH and distance != 0:
                    diff_factor = (distance - CHAIN_MAX_LENGTH) / distance;
                    p1_new_pos = player1.pos + delta * diff_factor
                    player1.pos.x = max(player1.rect.width // 2,
                                        min(p1_new_pos.x, SCREEN_WIDTH - player1.rect.width // 2));
                    player1.pos.y = max(player1.rect.height // 2,
                                        min(p1_new_pos.y, SCREEN_HEIGHT - player1.rect.height // 2));
                    player1.rect.center = player1.pos
            elif player2.is_alive and not player1.is_alive and player1.death_pos:
                delta = player1.death_pos - player2.pos;
                distance = delta.length()
                if distance > CHAIN_MAX_LENGTH and distance != 0:
                    diff_factor = (distance - CHAIN_MAX_LENGTH) / distance;
                    p2_new_pos = player2.pos + delta * diff_factor
                    player2.pos.x = max(player2.rect.width // 2,
                                        min(p2_new_pos.x, SCREEN_WIDTH - player2.rect.width // 2));
                    player2.pos.y = max(player2.rect.height // 2,
                                        min(p2_new_pos.y, SCREEN_HEIGHT - player2.rect.height // 2));
                    player2.rect.center = player2.pos

    elif game_state == STATE_BOSS_DEFEATED:
        # 玩家可自由移動，並檢查兩位玩家是否都在 boss_defeated_area_rect 上
        player1.update_movement(None, None, None, None, effect_manager, dt)
        player2.update_movement(None, None, None, None, effect_manager, dt)
        for _ in range(CHAIN_ITERATIONS):
            if player1.is_alive and player2.is_alive:
                p1_pos_vec = player1.pos
                p2_pos_vec = player2.pos
                delta = p2_pos_vec - p1_pos_vec
                distance = delta.length()
                if distance > CHAIN_MAX_LENGTH and distance != 0:
                    diff = (distance - CHAIN_MAX_LENGTH) / distance
                    p1_new_pos = player1.pos + delta * 0.5 * diff
                    p2_new_pos = player2.pos - delta * 0.5 * diff
                    player1.pos.x = max(player1.rect.width // 2,
                                        min(p1_new_pos.x, SCREEN_WIDTH - player1.rect.width // 2))
                    player1.pos.y = max(player1.rect.height // 2,
                                        min(p1_new_pos.y, SCREEN_HEIGHT - player1.rect.height // 2))
                    player2.pos.x = max(player2.rect.width // 2,
                                        min(p2_new_pos.x, SCREEN_WIDTH - player2.rect.width // 2))
                    player2.pos.y = max(player2.rect.height // 2,
                                        min(p2_new_pos.y, SCREEN_HEIGHT - player2.rect.height // 2))
                    player1.rect.center = player1.pos
                    player2.rect.center = player2.pos
            elif player1.is_alive and not player2.is_alive and player2.death_pos:
                delta = player2.death_pos - player1.pos
                distance = delta.length()
                if distance > CHAIN_MAX_LENGTH and distance != 0:
                    diff_factor = (distance - CHAIN_MAX_LENGTH) / distance
                    p1_new_pos = player1.pos + delta * diff_factor
                    player1.pos.x = max(player1.rect.width // 2,
                                        min(p1_new_pos.x, SCREEN_WIDTH - player1.rect.width // 2))
                    player1.pos.y = max(player1.rect.height // 2,
                                        min(p1_new_pos.y, SCREEN_HEIGHT - player1.rect.height // 2))
                    player1.rect.center = player1.pos
            elif player2.is_alive and not player1.is_alive and player1.death_pos:
                delta = player1.death_pos - player2.pos
                distance = delta.length()
                if distance > CHAIN_MAX_LENGTH and distance != 0:
                    diff_factor = (distance - CHAIN_MAX_LENGTH) / distance
                    p2_new_pos = player2.pos + delta * diff_factor
                    player2.pos.x = max(player2.rect.width // 2,
                                        min(p2_new_pos.x, SCREEN_WIDTH - player2.rect.width // 2))
                    player2.pos.y = max(player2.rect.height // 2,
                                        min(p2_new_pos.y, SCREEN_HEIGHT - player2.rect.height // 2))
                    player2.rect.center = player2.pos

        if boss_defeated_area_rect:
            p1_in = player1.rect.colliderect(boss_defeated_area_rect)
            p2_in = player2.rect.colliderect(boss_defeated_area_rect)
            if p1_in and p2_in:
                game_state = STATE_ASK_CAMERA

    elif game_state == STATE_CAMERA_INPUT:
        if camera_capture_active and not player_name_input_active and not post_capture_prompt_active:
            process_camera_frame()


    # --- 音樂播放控制 ---
    if game_state == STATE_START_SCREEN and last_game_state != STATE_START_SCREEN:
        if not start_screen_music_played :
            pygame.mixer.music.load('game_music/xDeviruchi - The Final of The Fantasy.wav')
            pygame.mixer.music.play(-1)
            start_screen_music_played = True
    elif game_state != STATE_START_SCREEN and last_game_state == STATE_START_SCREEN:
        start_screen_music_played = False # Allow it to restart if we return to start screen

    last_game_state = game_state

    screen.fill(BLACK)

    # --- 平鋪 floor.png 作為背景 ---
    if (
        (game_state == STATE_PLAYING and current_level_index in [0, 1, 2]) or
        game_state == STATE_BOSS_LEVEL or
        game_state == STATE_BOSS_DEFEATED or
        (game_state == STATE_PAUSED and state_before_pause in [STATE_PLAYING, STATE_BOSS_LEVEL, STATE_BOSS_DEFEATED])
    ):
        for y in range(0, SCREEN_HEIGHT, floor_tile_height):
            for x in range(0, SCREEN_WIDTH, floor_tile_width):
                screen.blit(floor_tile, (x, y))

    if game_state == STATE_PLAYING or (game_state == STATE_PAUSED and state_before_pause == STATE_PLAYING):
        current_lw_alpha = effect_manager.get_laser_wall_alpha() #
        for wall_sprite in laser_wall_sprites: #
            if hasattr(wall_sprite, 'update_visuals'): wall_sprite.update_visuals(current_lw_alpha) #
        laser_wall_sprites.draw(screen) #
        # goal_sprites.draw(screen) # 這一行是多餘的，下面的迴圈已經處理了
        for goal_sprite in goal_sprites: goal_sprite.draw(screen) #
        for coop_box_item in coop_box_group: coop_box_item.draw(screen) #
        for spike in spike_trap_group:
            spike.update(dt);
            spike.draw(screen) #
        fruit_sprites.draw(screen); #
        warning_sprites.draw(screen); #
        meteor_sprites.draw(screen) #
        player_sprites.draw(screen) #

    elif game_state == STATE_BOSS_LEVEL or (game_state == STATE_PAUSED and state_before_pause == STATE_BOSS_LEVEL):
        if boss_enemy:
            boss_enemy.draw(screen) #
        throwable_objects_group.draw(screen) #
        if player1.held_object:
            player1.held_object.draw(screen) #
        if boss_enemy and hasattr(boss_enemy, 'projectiles'): boss_enemy.projectiles.draw(screen) # Draw projectiles #
        player_sprites.draw(screen) #

    # 新增：在 BOSS_DEFEATED 狀態下繪製正方形區域
    if game_state == STATE_BOSS_DEFEATED:
        if boss_defeated_area_rect:
            # 使用 floor_ladder_img 填充 boss_defeated_area_rect 區域
            img = pygame.transform.scale(floor_ladder_img, (boss_defeated_area_rect.width, boss_defeated_area_rect.height))
            screen.blit(img, boss_defeated_area_rect.topleft)
            pygame.draw.rect(screen, (255, 255, 255), boss_defeated_area_rect, 4)
        player_sprites.draw(screen)

    if game_state in [STATE_PLAYING, STATE_BOSS_LEVEL, STATE_GAME_OVER, STATE_BOSS_DEFEATED] or \
            (game_state == STATE_PAUSED and state_before_pause in [STATE_PLAYING, STATE_BOSS_LEVEL]):
        draw_game_state_messages() #

    if game_state == STATE_START_SCREEN: #
        screen.blit(default_menu_background, (0, 0))  # Draw the background image
        title_text = font_large.render("雙人合作遊戲 Demo", True, TEXT_COLOR); #
        screen.blit(title_text,
                    (SCREEN_WIDTH // 2 - title_text.get_width() // 2, SCREEN_HEIGHT // 4 - 30)) # Adjusted Y #

        for i, option_text in enumerate(start_menu_options): #
            color = MENU_SELECTED_OPTION_COLOR if i == start_menu_selected_index else MENU_OPTION_COLOR #
            text_surf = font_menu.render(option_text, True, color) #
            menu_height = len(start_menu_options) * 70 #
            base_y = SCREEN_HEIGHT // 2 - menu_height // 2 + 100 #
            text_rect = text_surf.get_rect(center=(SCREEN_WIDTH // 2, base_y + i * 70)) #
            screen.blit(text_surf, text_rect) #

    elif game_state == STATE_LEVEL_SELECT: # NEW #
        draw_level_select_menu() #

    elif game_state == STATE_PAUSED: # NEW #
        draw_pause_menu() #

    elif game_state == STATE_ASK_CAMERA: #
        ask_text = font_small.render("啟用攝影機擷取頭像? (Y / N)", True, TEXT_COLOR) #
        screen.blit(ask_text, (SCREEN_WIDTH // 2 - ask_text.get_width() // 2, SCREEN_HEIGHT // 2 - 20)) #

    elif game_state == STATE_CAMERA_INPUT:
        base_y_offset = SCREEN_HEIGHT // 2 - 200 #
        if player_name_input_active: #
            name_prompt_text = font_small.render("請輸入隊伍/玩家名 (Enter 確認):", True, TEXT_COLOR) #
            screen.blit(name_prompt_text, (SCREEN_WIDTH // 2 - name_prompt_text.get_width() // 2, base_y_offset)) #
            name_field_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, base_y_offset + 40, 300, 40) #
            pygame.draw.rect(screen, WHITE, name_field_rect, 2) #
            name_input_surf = font_small.render(current_player_name, True, WHITE) #
            screen.blit(name_input_surf, (name_field_rect.x + 5, name_field_rect.y + (
                        name_field_rect.height - name_input_surf.get_height()) // 2)) #
            if pygame.time.get_ticks() % 1000 < 500: # Cursor blink #
                cursor_x = name_field_rect.x + 5 + name_input_surf.get_width() #
                if cursor_x < name_field_rect.right - 5: #
                    pygame.draw.line(screen, WHITE, (cursor_x, name_field_rect.y + 5),
                                     (cursor_x, name_field_rect.y + name_field_rect.height - 5), 2) #
        elif camera_capture_active and not post_capture_prompt_active: # Capturing phase #
            player_text = f"玩家 {current_capture_player_index + 1}" #
            capture_title_text = font_small.render(f"{player_text} 頭像擷取", True, TEXT_COLOR) #
            screen.blit(capture_title_text,
                        (SCREEN_WIDTH // 2 - capture_title_text.get_width() // 2, base_y_offset - 40)) #
            if camera_frame_surface: #
                feed_x = (SCREEN_WIDTH - camera_frame_surface.get_width()) // 2 #
                feed_y = base_y_offset #
                screen.blit(camera_frame_surface, (feed_x, feed_y)) #
            else: #
                init_cam_text = font_small.render("正在初始化攝影機...", True, TEXT_COLOR) #
                screen.blit(init_cam_text,
                            (SCREEN_WIDTH // 2 - init_cam_text.get_width() // 2, SCREEN_HEIGHT // 2 - 20)) #
            prompt_str = f"對準鏡頭: (A)擷取{player_text} / (S)略過{player_text} / (Q)完成並到排行榜" #
            capture_prompt_surf = font_tiny.render(prompt_str, True, TEXT_COLOR) #
            screen.blit(capture_prompt_surf,
                        (SCREEN_WIDTH // 2 - capture_prompt_surf.get_width() // 2, SCREEN_HEIGHT - 70)) #
        elif post_capture_prompt_active: # Post capture/skip options for current player #
            player_text = f"玩家 {current_capture_player_index + 1}" #
            status_text_str = "" #
            if current_capture_player_index == 0: #
                status_text_str = "照片已儲存!" if captured_face_image_path_p1 else "照片已略過。" #
            else: # P2 #
                status_text_str = "照片已儲存!" if captured_face_image_path_p2 else "照片已略過。" #
            status_surf = font_small.render(f"{player_text}: {status_text_str}", True, (0, 255, 0) if (
                                                                                                                  current_capture_player_index == 0 and captured_face_image_path_p1) or (
                                                                                                                  current_capture_player_index == 1 and captured_face_image_path_p2) else TEXT_COLOR) #
            screen.blit(status_surf,
                        (SCREEN_WIDTH // 2 - status_surf.get_width() // 2, base_y_offset + 50)) # Match y-level #
            options_y_start = base_y_offset + 100 # options below status text #
            if current_capture_player_index == 0: # P1 options #
                opt_str1 = f"(R)重拍{player_text}" #
                opt_str2 = "(N)擷取玩家2頭像" #
                opt_str3 = "(F)完成 (僅儲存目前結果)" #
                screen.blit(font_tiny.render(opt_str1, True, TEXT_COLOR),
                            (SCREEN_WIDTH // 2 - font_tiny.render(opt_str1, True, TEXT_COLOR).get_width() // 2,
                             options_y_start)) #
                screen.blit(font_tiny.render(opt_str2, True, TEXT_COLOR),
                            (SCREEN_WIDTH // 2 - font_tiny.render(opt_str2, True, TEXT_COLOR).get_width() // 2,
                             options_y_start + 30)) #
                screen.blit(font_tiny.render(opt_str3, True, TEXT_COLOR),
                            (SCREEN_WIDTH // 2 - font_tiny.render(opt_str3, True, TEXT_COLOR).get_width() // 2,
                             options_y_start + 60)) #
            else: # P2 options #
                opt_str1 = f"(R)重拍{player_text}" #
                opt_str2 = "(B)返回玩家1選項" #
                opt_str3 = "(F)完成並儲存" #
                screen.blit(font_tiny.render(opt_str1, True, TEXT_COLOR),
                            (SCREEN_WIDTH // 2 - font_tiny.render(opt_str1, True, TEXT_COLOR).get_width() // 2,
                             options_y_start)) #
                screen.blit(font_tiny.render(opt_str2, True, TEXT_COLOR),
                            (SCREEN_WIDTH // 2 - font_tiny.render(opt_str2, True, TEXT_COLOR).get_width() // 2,
                             options_y_start + 30)) #
                screen.blit(font_tiny.render(opt_str3, True, TEXT_COLOR),
                            (SCREEN_WIDTH // 2 - font_tiny.render(opt_str3, True, TEXT_COLOR).get_width() // 2,
                             options_y_start + 60)) #

    elif game_state == STATE_SHOW_LEADERBOARD: #
        draw_leaderboard_screen() #

    if game_state == STATE_PLAYING or game_state == STATE_BOSS_LEVEL: #
        current_revive_initiator = None; #
        potential_target_player = None # #
        if player1.is_alive and not player2.is_alive and player2.death_pos: # #
            if player1.pos.distance_to(player2.death_pos) <= REVIVAL_RADIUS: # #
                if keys[REVIVE_KEYP1]: current_revive_initiator = player1; potential_target_player = player2; # #
        elif player2.is_alive and not player1.is_alive and player1.death_pos: # #
            if player2.pos.distance_to(player1.death_pos) <= REVIVAL_RADIUS: # #
                if keys[REVIVE_KEYP2]: current_revive_initiator = player2; potential_target_player = player1; # #

        if current_revive_initiator and potential_target_player: #
            if revive_target != potential_target_player: revive_target = potential_target_player; revive_progress = 0 # #
            revive_progress += dt # #
        else: # Logic to reset progress if key is released or conditions change #
            reset_progress_flag = True #
            if revive_target == player2 and keys[
                REVIVE_KEYP1] and player1.is_alive and player2.death_pos and player1.pos.distance_to(
                    player2.death_pos) <= REVIVAL_RADIUS: #
                reset_progress_flag = False #
            if revive_target == player1 and keys[
                REVIVE_KEYP2] and player2.is_alive and player1.death_pos and player2.pos.distance_to(
                    player1.death_pos) <= REVIVAL_RADIUS: #
                reset_progress_flag = False #
            if reset_progress_flag: #
                revive_progress = 0 #

        if revive_progress >= REVIVE_HOLD_TIME and revive_target is not None: # #
            if revive_target == player2: #
                player2.revive() # #
            elif revive_target == player1: #
                player1.revive() # #
            revive_progress = 0; #
            revive_target = None # #

        if revive_target is not None and revive_progress > 0: # #
            percentage = min(revive_progress / REVIVE_HOLD_TIME, 1.0); #
            center_pos_death = None # #
            if revive_target == player1 and player1.death_pos: #
                center_pos_death = player1.death_pos # #
            elif revive_target == player2 and player2.death_pos: #
                center_pos_death = player2.death_pos # #
            if center_pos_death: #
                radius = 20; #
                arc_rect_center_x = int(center_pos_death.x) #
                arc_rect_center_y = int(
                    center_pos_death.y - PLAYER_RADIUS - radius * 0.5) # Position above dead player #
                arc_rect = pygame.Rect(arc_rect_center_x - radius, arc_rect_center_y - radius, radius * 2,
                                       radius * 2) #
                pygame.draw.circle(screen, (80, 80, 80, 150) if pygame.SRCALPHA else (80, 80, 80), arc_rect.center,
                                   radius, 2) # #
                start_angle_rad = -math.pi / 2; #
                end_angle_rad = start_angle_rad + (percentage * 2 * math.pi) #
                if percentage > 0.01: pygame.draw.arc(screen, REVIVE_PROMPT_COLOR, arc_rect, start_angle_rad,
                                                      end_angle_rad, 4) #

    if show_save_feedback:
        feedback_surface = font_tiny.render("遊戲已存檔", True, SAVE_MESSAGE_COLOR)
        feedback_rect = feedback_surface.get_rect(topright=(SCREEN_WIDTH - 10, 10))
        screen.blit(feedback_surface, feedback_rect)

    # Draw a white line between player1 and player2 only during gameplay
    if game_state in [STATE_PLAYING, STATE_BOSS_LEVEL, STATE_BOSS_DEFEATED]:
        pygame.draw.line(screen, (255, 255, 255), (player1.pos.x, player1.pos.y), (player2.pos.x, player2.pos.y), 2)

    show_opencv_paint_window() #
    pygame.display.flip() #

release_camera_resources()
pygame.quit()
