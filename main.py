import pygame
import cv2
import numpy as np
import math
from player import *
from boss_entities import Boss
import random
import json
import os
from music import *

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
GOAL_P1_COLOR = (100, 100, 255)
GOAL_P2_COLOR = (255, 100, 100)
TEXT_COLOR = (200, 200, 200)
REVIVE_PROMPT_COLOR = (50, 200, 50)
COOP_BOX_COLOR = (180, 140, 0)
SCORE_FRUIT_COLOR = (255, 223, 0)
SCORE_FRUIT_VALUE = 1
MAX_TOTAL_SCORE = 3

LEADERBOARD_FILE = "leaderboard.json"
MAX_LEADERBOARD_ENTRIES = 10 # Show top 10
FACE_IMAGE_SAVE_DIR = "CatchFace"
LEADERBOARD_FACE_SIZE = (60, 60)

# 玩家參數
CHAIN_MAX_LENGTH = 400
CHAIN_ITERATIONS = 5
REVIVAL_RADIUS = CHAIN_MAX_LENGTH  #
REVIVE_KEYP1 = pygame.K_f  #
REVIVE_KEYP2 = pygame.K_PERIOD  #

# 協力推箱子常數
COOP_BOX_SIZE = 40  #
COOP_BOX_SPEED = 2  #
COOP_BOX_PUSH_RADIUS = 60  #

# 地刺參數
SAFE_COLOR = (220, 220, 220)  #
DANGER_COLOR = (220, 40, 40)  #

# 遊戲狀態
STATE_START_SCREEN = 4  #
STATE_PLAYING = 0  #
STATE_GAME_OVER = 1  #
STATE_LEVEL_COMPLETE = 2  # No longer used directly for "all levels", see PRE_BOSS
STATE_PRE_BOSS_COMPLETE = 3  # This state will no longer be actively used for a waiting screen
STATE_BOSS_LEVEL = 5  # New state for Boss Level
STATE_BOSS_DEFEATED = 6  # New state for when Boss is defeated
STATE_ASK_CAMERA = 9
STATE_CAMERA_INPUT = 7
STATE_SHOW_LEADERBOARD = 8

# --- 果實相關常數 ---
FRUIT_RADIUS = 15  #
FRUIT_EFFECT_DURATION = 30.0  #

# 果實顏色
MIRROR_FRUIT_COLOR = (255, 215, 0)  #
INVISIBLE_WALL_COLOR = (138, 43, 226)  #
VOLCANO_FRUIT_COLOR = (255, 69, 0)  #

# 火山效果相關常數
METEOR_WARNING_TIME = 1.5  #
METEOR_FALL_TIME = 0.5  #
METEOR_SIZE = 75  #
METEOR_COLOR = (139, 69, 19)  #
WARNING_COLOR = (255, 255, 0)  #

# Boss Level Item Spawn Point (P2 "draws" here if P1 not available)
ITEM_SPAWN_POS_DEFAULT = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50)

# --- 檔案相關 ---
SAVE_FILE = "savegame.json"

# --- Pygame 初始化 ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("雙人合作遊戲 Demo - 果實能力 & Boss")  # Updated Caption
clock = pygame.time.Clock()
if not os.path.exists(FACE_IMAGE_SAVE_DIR):
    os.makedirs(FACE_IMAGE_SAVE_DIR)

# --- 音樂檔案路徑 ---
LEVEL_1_MUSIC = os.path.join("game_music", "04 - Silent Forest.mp3")
BOSS_MUSIC = os.path.join("game_music", "10 - Lost Shrine.mp3")

# 圖片載入
box_img = pygame.image.load("box.png").convert_alpha()  #
spike_trap_img_out = pygame.image.load("spike_trap_out.png").convert_alpha()  #
spike_trap_img_in = pygame.image.load("spike_trap_in.png").convert_alpha()  #

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
    else:
        print("警告：找不到中文字體，遊戲中的中文可能無法正確顯示")
        font_small = pygame.font.Font(None, 36)
        font_large = pygame.font.Font(None, 74)
        font_tiny = pygame.font.Font(None, 24)
        font_effect = pygame.font.Font(None, 18)
except Exception as e:
    print(f"載入字體時出錯：{e}")
    font_small = pygame.font.Font(None, 36)
    font_large = pygame.font.Font(None, 74)
    font_tiny = pygame.font.Font(None, 24)
    font_effect = pygame.font.Font(None, 18)

# --- OpenCV 視窗準備 (Not used by fruits) ---
use_opencv = False  #
opencv_window_name = "P2 Paint Area (OpenCV)"  #
paint_surface_width = 400  #
paint_surface_height = 300  #
paint_surface = np.zeros((paint_surface_height, paint_surface_width, 3), dtype=np.uint8) + 200  #

# --- Global game variables ---
game_time_elapsed = 0.0
current_score = 0
leaderboard_data = []

# Variables for camera input state
camera_capture_active = False
player_name_input_active = False
current_player_name = ""
captured_face_image_path = None
current_leaderboard_entry_index = None
final_game_time = 0.0
final_player_score = 0
photo_taken_prompt_active = False # After a photo is taken, ask what to do next.

# OpenCV related
cap = None
face_cascade = None
camera_frame_surface = None # Pygame surface for camera feed
loaded_face_images_cache = {} # Cache for loaded face images for leaderboard

def show_opencv_paint_window():  #
    if use_opencv:
        cv2.imshow(opencv_window_name, paint_surface)
        key = cv2.waitKey(1) & 0xFF

# --- 果實類別 --- (Copied from original)
class Fruit(pygame.sprite.Sprite):  #
    def __init__(self, x, y, fruit_type):
        super().__init__()
        self.fruit_type = fruit_type
        self.image = pygame.Surface([FRUIT_RADIUS * 2, FRUIT_RADIUS * 2], pygame.SRCALPHA)
        if fruit_type == "mirror":
            color = MIRROR_FRUIT_COLOR
        elif fruit_type == "invisible_wall":
            color = INVISIBLE_WALL_COLOR
        elif fruit_type == "volcano":
            color = VOLCANO_FRUIT_COLOR
        elif fruit_type == "score":
            color = SCORE_FRUIT_COLOR
        else:
            color = (255, 255, 255)
        pygame.draw.circle(self.image, color, (FRUIT_RADIUS, FRUIT_RADIUS), FRUIT_RADIUS)
        pygame.draw.circle(self.image, WHITE, (FRUIT_RADIUS, FRUIT_RADIUS), FRUIT_RADIUS, 2)
        self.rect = self.image.get_rect(center=(x, y))

# --- 流星類別 (火山爆發效果) --- (Copied from original)
class Meteor(pygame.sprite.Sprite):  #
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
class Warning(pygame.sprite.Sprite):  #
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
            return True  # Indicate meteor should spawn
        return False

# --- 效果管理器 --- (Copied from original)
class EffectManager:  #
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
                self.effects["mirror_p1"]["active"] = True; self.effects["mirror_p1"]["timer"] = FRUIT_EFFECT_DURATION
            elif player_id == 1:
                self.effects["mirror_p2"]["active"] = True; self.effects["mirror_p2"]["timer"] = FRUIT_EFFECT_DURATION
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
                        time_in_fade_out = time_in_visible_phase - fade_time; target_alpha = int(
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
class LaserWall(pygame.sprite.Sprite):  #
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
class Goal(pygame.sprite.Sprite):  #
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
class CoopBox(pygame.sprite.Sprite):  #
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
            self.image = pygame.Surface([self.display_size, self.display_size]); self.image.fill(COOP_BOX_COLOR)

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
        img_rect = self.image.get_rect(center=self.rect.center); surface.blit(self.image, img_rect)

# ---地刺類別--- (Copied from original)
class SpikeTrap(pygame.sprite.Sprite):  #
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
        self.timer += dt; phase = self.timer % self.cycle_time; self.active = phase < self.out_time

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
levels_data = [  #
    {  # Level 1 Data (existing)
        "player1_start": (100, SCREEN_HEIGHT // 2), "player2_start": (150, SCREEN_HEIGHT // 2),
        "goal1_pos": (SCREEN_WIDTH - 50, 150), "goal2_pos": (SCREEN_WIDTH - 50, SCREEN_HEIGHT - 150),
        "laser_walls": [(SCREEN_WIDTH // 2 - 10, 150, 20, SCREEN_HEIGHT - 300),
                        (200, SCREEN_HEIGHT // 2 - 10, SCREEN_WIDTH // 2 - 200 - 10, 10),
                        (SCREEN_WIDTH // 2 + 10, SCREEN_HEIGHT // 2 - 10, SCREEN_WIDTH // 2 - 20 - 10, 10)],
        "coop_box_start": [(SCREEN_WIDTH // 4, SCREEN_HEIGHT // 4), (SCREEN_WIDTH // 4 + 50, SCREEN_HEIGHT // 4 + 50)],
        "spike_traps": [(40, 40, 40, 40, 1.0, 2.0, 0.0), (100, 40, 40, 40, 0.7, 1.5, 0.5),
                        (160, 40, 40, 40, 1.2, 1.0, 1.0)],
        "fruits": [(SCREEN_WIDTH // 2, 130, "mirror"), (200, 100, "invisible_wall"),
                   (SCREEN_WIDTH - 200, SCREEN_HEIGHT - 100, "volcano")]
    },
    {  # Level 2 Data (existing)
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
    },{
        "player1_start": (50, SCREEN_HEIGHT // 2 + 40), "player2_start": (50, SCREEN_HEIGHT // 2 - 30),
        "goal1_pos": (SCREEN_WIDTH - 50, 190), "goal2_pos": (SCREEN_WIDTH - 50, SCREEN_HEIGHT - 190),
        "laser_walls": [  # 衡的外面
            (0, 100, 500, 20), (0, SCREEN_HEIGHT - 100, 500, 20),
            (600, 100, 150, 20), (600, SCREEN_HEIGHT - 100, 150, 20),
            (800, 100, 90, 20), (800, SCREEN_HEIGHT - 100, 100, 20),
            # 值得裡面
            (80, 120, 20, 150), (80, SCREEN_HEIGHT - 260, 20, 180),
            (160, 210, 20, 150), (160, SCREEN_HEIGHT - 340, 20, 180),
            (240, 120, 20, 150), (240, SCREEN_HEIGHT - 260, 20, 180),
            (320, 210, 20, 150), (320, SCREEN_HEIGHT - 340, 20, 180),
            (400, 80, 20, 180), (400, SCREEN_HEIGHT - 250, 20, 180),
            (480, 210, 20, 150), (480, SCREEN_HEIGHT - 340, 20, 180),
            # 種兼職的
            (560, 120, 20, 150), (560, SCREEN_HEIGHT - 260, 20, 180),
            # 終點乓圈圈
            (980, 330, 100, 20), (980, SCREEN_HEIGHT - 330, 150, 20),
            (950, 150, 20, 150), (950, SCREEN_HEIGHT - 300, 20, 150),

            (850, 220, 20, 150), (850, SCREEN_HEIGHT - 350, 20, 180),

            (650, SCREEN_HEIGHT // 2 - 40, 20, 170),
            (750, 100, 20, 220), (750, SCREEN_HEIGHT - 300, 20, 220),
            (0, SCREEN_HEIGHT // 2, 500, 20)],
        "coop_box_start": [(1010, 120), (1050, 120), (SCREEN_WIDTH - 70, SCREEN_HEIGHT - 120),
                           (SCREEN_WIDTH - 30, SCREEN_HEIGHT - 120)],
        "spike_traps": [(750 ,325, 40, 40, 1.5, 2.5, 0.0),(750 ,365, 40, 40, 1.5, 2.5, 0.0),
                        (75 ,300, 40, 40, 1.5, 2.5, 1.5),(155 ,570, 40, 40, 1.5, 2.5, 0.4),
                        (235 ,300, 40, 40, 1.5, 2.5, 0.3),(315 ,570, 40, 40, 1.5, 2.5, 1.6),
                        (395 ,300, 40, 40, 1.5, 2.5, 2.5),(475 ,570, 40, 40, 1.5, 2.5, 0.5),
                        (40, 40, 40, 40, 1.0, 2.0, 0.0), (100, 40, 40, 40, 0.7, 1.5, 0.5),
                        (160, 40, 40, 40, 1.2, 1.0, 1.0)],
        "fruits": [(SCREEN_WIDTH // 2, 130, "mirror"), (200, 100, "invisible_wall"),
                   (SCREEN_WIDTH - 200, SCREEN_HEIGHT - 100, "volcano")]
    },
    # Boss level will be handled separately, not in this list structure.
]
current_level_index = 0  #

# --- 遊戲物件群組 ---
all_sprites = pygame.sprite.Group()  #
laser_wall_sprites = pygame.sprite.Group()  #
goal_sprites = pygame.sprite.Group()  #
player_sprites = pygame.sprite.Group()  #
coop_box_group = pygame.sprite.Group()  #
spike_trap_group = pygame.sprite.Group()  #
fruit_sprites = pygame.sprite.Group()  #
meteor_sprites = pygame.sprite.Group()  #
warning_sprites = pygame.sprite.Group()  #

# Boss Level Specific Groups
boss_group = pygame.sprite.GroupSingle()  # For single boss
throwable_objects_group = pygame.sprite.Group()
# boss_projectiles are managed within the Boss class instance's group

# --- 遊戲物件實體 ---
player1 = Player(0, 0, PLAYER1_COLOR, PLAYER1_DEAD_COLOR,
                 {'up': pygame.K_w, 'down': pygame.K_s, 'left': pygame.K_a, 'right': pygame.K_d}, 0)  #
player2 = Player(0, 0, PLAYER2_COLOR, PLAYER2_DEAD_COLOR,
                 {'up': pygame.K_UP, 'down': pygame.K_DOWN, 'left': pygame.K_LEFT, 'right': pygame.K_RIGHT}, 1)  #
player_sprites.add(player1, player2)

goal1 = Goal(0, 0, GOAL_P1_COLOR, 0)  #
goal2 = Goal(0, 0, GOAL_P2_COLOR, 1)  #
# coop_box is loaded per level

effect_manager = EffectManager()  #
boss_enemy = None  # Will be initialized for boss level

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

def add_leaderboard_entry(name, time_val, score_val, image_path):
    global leaderboard_data
    # Prevent duplicate entries for the same play session if user re-captures for same name
    # This simple add just appends; more sophisticated logic could update an existing entry
    # if player chose to "change name" and re-captured.
    # For this flow, each successful capture flow adds a new potential entry.
    leaderboard_data.append({
        "name": name,
        "time": round(time_val, 2), # Store time with 2 decimal places
        "score": score_val,
        "face_image_path": image_path
    })

load_leaderboard() # Load at game start

def initialize_camera_for_capture():
    global cap, face_cascade, camera_capture_active, game_state
    if cap and cap.isOpened(): # Already initialized and open
        camera_capture_active = True # Ensure flag is set
        return

    try:
        pictPath = cv2.data.haarcascades + 'haarcascade_frontalface_alt2.xml'
        if not os.path.exists(pictPath):
            print(f"錯誤：找不到 Haar cascade 檔案於 {pictPath}")
            game_state = STATE_SHOW_LEADERBOARD
            return

        face_cascade = cv2.CascadeClassifier(pictPath)
        if face_cascade.empty():
            print("錯誤：無法載入 Haar cascade。")
            game_state = STATE_SHOW_LEADERBOARD
            return

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("錯誤：無法開啟攝影機。")
            cap = None
            game_state = STATE_SHOW_LEADERBOARD
            return
        camera_capture_active = True
        print("攝影機已初始化。")
    except Exception as e:
        print(f"攝影機初始化時發生例外狀況：{e}")
        release_camera_resources()
        game_state = STATE_SHOW_LEADERBOARD

def release_camera_resources():
    global cap, camera_capture_active, camera_frame_surface
    if cap:
        cap.release()
        cap = None
    camera_capture_active = False
    camera_frame_surface = None
    cv2.destroyAllWindows() # Ensure any OpenCV windows are closed
    print("攝影機資源已釋放。")

def process_camera_frame():
    global cap, face_cascade, camera_frame_surface, game_state # Added game_state
    if not camera_capture_active or not cap or not cap.isOpened() or not face_cascade:
        return

    ret, frame_bgr = cap.read()
    if not ret:
        print("錯誤：無法從攝影機讀取畫面。")
        release_camera_resources()
        game_state = STATE_SHOW_LEADERBOARD # Fallback if camera fails
        return

    frame_bgr = cv2.flip(frame_bgr, 1) # Mirror
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))

    # Create a copy for drawing rectangles, so original frame for Pygame is clean until faces are drawn on it
    display_frame_bgr = frame_bgr.copy()
    for (x, y, w, h) in faces:
        cv2.rectangle(display_frame_bgr, (x, y), (x + w, y + h), (0, 255, 0), 2) # Green rectangle

    frame_rgb = cv2.cvtColor(display_frame_bgr, cv2.COLOR_BGR2RGB)

    target_width, target_height = min(640, SCREEN_WIDTH - 100), min(480, SCREEN_HEIGHT - 200)
    frame_resized = cv2.resize(frame_rgb, (target_width, target_height))

    temp_surface = pygame.surfarray.make_surface(frame_resized)
    camera_frame_surface = pygame.transform.rotate(temp_surface, -90)

def handle_photo_capture():
    global cap, face_cascade, current_player_name, captured_face_image_path, photo_taken_prompt_active
    global final_game_time, final_player_score, current_leaderboard_entry_index  # Make sure these are accessible

    if not camera_capture_active or not cap or not cap.isOpened() or not face_cascade:
        return False

    ret, frame_bgr = cap.read()
    if not ret:
        print("拍照錯誤：無法讀取畫面。")
        return False
    frame_bgr = cv2.flip(frame_bgr, 1)  # Ensure consistent orientation with preview

    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))

    if len(faces) > 0:
        x, y, w, h = faces[0]  # Capture the first detected face
        face_crop = frame_bgr[y:y + h, x:x + w]
        face_resize = cv2.resize(face_crop, LEADERBOARD_FACE_SIZE)

        # Sanitize player name for filename
        sane_name = "".join(c if c.isalnum() else "_" for c in current_player_name.strip())
        if not sane_name: sane_name = "player"
        new_image_path = None

        index = 1
        base_filename = os.path.join(FACE_IMAGE_SAVE_DIR, f"{sane_name}_{{}}.png")
        filename_to_save = base_filename.format(index)
        while os.path.exists(filename_to_save):
            index += 1
            filename_to_save = base_filename.format(index)
        new_image_path = filename_to_save
        try:
            if captured_face_image_path and os.path.exists(captured_face_image_path):
                try:
                    print(f"準備刪除先前拍攝的照片: {captured_face_image_path}")
                    os.remove(captured_face_image_path)  # <--- 刪除舊照片檔案
                    print(f"已成功刪除: {captured_face_image_path}")
                except OSError as e:
                    print(f"刪除舊照片 {captured_face_image_path} 失敗: {e}")

            print(f"Attempting to save image to: '{new_image_path}'")  # <-- ADD THIS LINE FOR DEBUGGING
            cv2.imwrite(new_image_path, face_resize)
            print(f"臉部影像已儲存至 {filename_to_save}")

            if current_leaderboard_entry_index is not None and \
                    0 <= current_leaderboard_entry_index < len(leaderboard_data):
                entry_to_update = leaderboard_data[current_leaderboard_entry_index]

                old_image_for_entry = entry_to_update.get("face_image_path")
                if old_image_for_entry and os.path.exists(
                        old_image_for_entry) and old_image_for_entry != new_image_path:
                    try:
                        os.remove(old_image_for_entry)
                        print(f"已成功刪除排行榜條目中的舊頭像: {old_image_for_entry}")
                    except OSError as e:
                        print(f"刪除排行榜條目舊頭像 {old_image_for_entry} 失敗: {e}")

                entry_to_update["face_image_path"] = new_image_path
                entry_to_update["name"] = current_player_name
                print(f"已更新排行榜紀錄索引 {current_leaderboard_entry_index} 的頭像為 {new_image_path}")
            else:
                add_leaderboard_entry(current_player_name, final_game_time, final_player_score, new_image_path)
                current_leaderboard_entry_index = len(leaderboard_data) - 1  # 記住這個新條目的索引
                print(f"已新增排行榜紀錄，新索引為: {current_leaderboard_entry_index}")

            captured_face_image_path = new_image_path  # <--- 更新全域變數，指向最新儲存的照片

            photo_taken_prompt_active = True  # 顯示後續選項提示
            return True
        except Exception as e:
            print(f"儲存影像時發生錯誤: {e}")
            return False
    else:
        print("未偵測到臉部以進行拍照。")
        return False

# --- Boss Level Setup Function ---
def setup_boss_level():
    global boss_enemy, game_state, game_time_elapsed
    # 播放Boss關卡音樂
    play_music(BOSS_MUSIC)
    # Clear regular level sprites if any could persist (though load_level should handle most)
    laser_wall_sprites.empty()
    goal_sprites.empty()
    coop_box_group.empty()
    spike_trap_group.empty()
    fruit_sprites.empty()  # No fruits in boss level by default
    meteor_sprites.empty()
    warning_sprites.empty()
    throwable_objects_group.empty()  # Clear any previous throwable items
    effect_manager.reset_all_effects()  # Reset any active fruit effects
    # Reset players to starting positions for boss arena
    player1.start_pos = pygame.math.Vector2(100, SCREEN_HEIGHT - 100)
    player2.start_pos = pygame.math.Vector2(150, SCREEN_HEIGHT - 100)
    player1.reset()
    player2.reset()

    # Initialize Boss
    boss_enemy = Boss(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4)
    boss_group.add(boss_enemy)

    # No laser walls, goals, coop boxes, spikes in this basic boss level setup. Can be added if needed.
    game_state = STATE_BOSS_LEVEL

def load_level(level_idx):  #
    global game_state, current_level_index
    if level_idx >= len(levels_data):
        setup_boss_level()  # Directly set up the boss level if all regular levels are done
        return


    level = levels_data[level_idx]
    current_level_index = level_idx  # Keep track of the actual level number being played

    play_music(LEVEL_1_MUSIC)

    laser_wall_sprites.empty();
    goal_sprites.empty();
    coop_box_group.empty()
    spike_trap_group.empty();
    fruit_sprites.empty();
    meteor_sprites.empty()
    warning_sprites.empty();
    throwable_objects_group.empty()  # Clear throwable from previous attempts
    effect_manager.reset_all_effects()
    game_time_elapsed = 0.0  # Reset timer for new regular level
    current_score = 0  # Reset score for new regular level

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
def save_game_state():
    global current_level_index, game_state, player1, player2, boss_enemy, effect_manager, throwable_objects_group

    if game_state != STATE_PLAYING and game_state != STATE_BOSS_LEVEL:
        print("只能在遊玩關卡或Boss戰時存檔。")
        return

    save_data = {
        "current_level_index": current_level_index,
        "game_state_on_save": game_state,
        "player1": {
            "pos_x": player1.pos.x,
            "pos_y": player1.pos.y,
            "is_alive": player1.is_alive,
            "facing_left": player1.facing_left, # 新增
            "death_pos_x": player1.death_pos.x if player1.death_pos else None,
            "death_pos_y": player1.death_pos.y if player1.death_pos else None,
            "held_object_info": None # 稍後處理可投擲物
        },
        "player2": {
            "pos_x": player2.pos.x,
            "pos_y": player2.pos.y,
            "is_alive": player2.is_alive,
            "facing_left": player2.facing_left, # 新增
            "death_pos_x": player2.death_pos.x if player2.death_pos else None,
            "death_pos_y": player2.death_pos.y if player2.death_pos else None,
            "can_spawn_item_timer": player2.can_spawn_item_timer
        },
        "effect_manager": {
            "effects": {},
        },
        "boss_level_data": None,
        "throwable_objects": [],
        "coop_boxes": [] # 新增: 用於儲存普通關卡的箱子位置
    }

    # 儲存效果狀態
    for key, effect_data_val in effect_manager.effects.items(): # 變數名修改避免與外層衝突
        save_data["effect_manager"]["effects"][key] = {
            "active": effect_data_val["active"],
            "timer": effect_data_val["timer"]
        }
        if "flash_timer" in effect_data_val:
             save_data["effect_manager"]["effects"][key]["flash_timer"] = effect_data_val["flash_timer"]
        if "current_alpha" in effect_data_val: # For invisible_wall
             save_data["effect_manager"]["effects"][key]["current_alpha"] = effect_data_val["current_alpha"]
        if "meteor_timer" in effect_data_val:
            save_data["effect_manager"]["effects"][key]["meteor_timer"] = effect_data_val["meteor_timer"]

    if game_state == STATE_BOSS_LEVEL:
        if boss_enemy: # 確保 boss_enemy 存在
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

        # 儲存可投擲物 (包含 P1 是否持有)
        player1_held_object_temp_id = -1
        if player1.held_object:
            player1_held_object_temp_id = id(player1.held_object) # 臨時標識

        for i, obj in enumerate(throwable_objects_group):
            obj_data = {
                "temp_id": id(obj), # 臨時標識
                "pos_x": obj.pos.x,
                "pos_y": obj.pos.y,
                "is_thrown": obj.is_thrown,
                "throw_velocity_x": obj.throw_velocity.x,
                "throw_velocity_y": obj.throw_velocity.y,
                "spawned_by_player_id": obj.spawned_by_player_id,
                "is_held_by_p1": (id(obj) == player1_held_object_temp_id) # 標記是否被P1持有
            }
            save_data["throwable_objects"].append(obj_data)
            if id(obj) == player1_held_object_temp_id: # 如果 P1 持有此物件
                save_data["player1"]["held_object_info"] = obj_data # 直接存儲物件信息

    elif game_state == STATE_PLAYING: # 儲存普通關卡中的協力推箱子位置
         for box in coop_box_group:
             save_data["coop_boxes"].append({
                 "pos_x": box.pos.x,
                 "pos_y": box.pos.y
             })

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

    try:
        with open(SAVE_FILE, 'r') as f:
            load_data = json.load(f)
        print(f"從 {SAVE_FILE} 載入遊戲狀態...")
    except FileNotFoundError:
        print(f"存檔 {SAVE_FILE} 未找到。開始新遊戲。")
        current_level_index = 0
        load_level(current_level_index)
        return
    except Exception as e:
        print(f"載入遊戲狀態時發生錯誤: {e}。開始新遊戲。")
        current_level_index = 0
        load_level(current_level_index)
        return

    # --- 清理現有的動態遊戲物件 ---
    laser_wall_sprites.empty()
    goal_sprites.empty()
    coop_box_group.empty()
    spike_trap_group.empty()
    fruit_sprites.empty()
    meteor_sprites.empty()
    warning_sprites.empty()
    boss_group.empty()
    throwable_objects_group.empty()
    if boss_enemy and hasattr(boss_enemy, 'projectiles'): # 清理Boss的投射物
        boss_enemy.projectiles.empty()
    # player_sprites 會在後面根據讀取到的玩家狀態重新加入

    current_level_index = load_data.get("current_level_index", 0)
    saved_game_state_type = load_data.get("game_state_on_save", STATE_PLAYING)

    # --- 恢復 Effect Manager ---
    effect_manager.reset_all_effects()
    loaded_effects_manager_data = load_data.get("effect_manager", {}).get("effects", {})
    for key, effect_save_data in loaded_effects_manager_data.items():
        if key in effect_manager.effects:
            effect_manager.effects[key]["active"] = effect_save_data.get("active", False)
            effect_manager.effects[key]["timer"] = effect_save_data.get("timer", 0)
            if "flash_timer" in effect_manager.effects[key] and "flash_timer" in effect_save_data:
                 effect_manager.effects[key]["flash_timer"] = effect_save_data["flash_timer"]
            if "current_alpha" in effect_manager.effects[key] and "current_alpha" in effect_save_data: # For invisible_wall
                 effect_manager.effects[key]["current_alpha"] = effect_save_data["current_alpha"]
            elif key == "invisible_wall": # Ensure default if not saved
                 effect_manager.effects[key]["current_alpha"] = effect_manager.default_laser_wall_alpha

            if "meteor_timer" in effect_manager.effects[key] and "meteor_timer" in effect_save_data:
                effect_manager.effects[key]["meteor_timer"] = effect_save_data["meteor_timer"]


    # --- 根據存檔的遊戲狀態類型載入關卡結構 ---
    if saved_game_state_type == STATE_BOSS_LEVEL:
        setup_boss_level() # 這會設定 game_state = STATE_BOSS_LEVEL 並重置玩家
    else: # 普通關卡
        if current_level_index >= len(levels_data):
            print("錯誤：存檔的關卡索引超出範圍。開始新遊戲。")
            current_level_index = 0
            load_level(current_level_index)
            return
        load_level(current_level_index) # 這會設定 game_state = STATE_PLAYING 並重置玩家
        # 恢復協力推箱子位置
        coop_box_group.empty() # 清空由 load_level 創建的預設箱子
        loaded_coop_boxes = load_data.get("coop_boxes", [])
        for box_data in loaded_coop_boxes:
            coop_box_group.add(CoopBox(box_data["pos_x"], box_data["pos_y"], img=box_img))


    game_state = saved_game_state_type # 確保 game_state 在 load_level/setup_boss_level 後被正確恢復

    # --- 恢復玩家狀態 ---
    player1.reset() # 先重置以清除舊狀態，尤其是 held_object
    p1_data = load_data.get("player1", {})
    player1.pos = pygame.math.Vector2(p1_data.get("pos_x", player1.start_pos.x), p1_data.get("pos_y", player1.start_pos.y))
    player1.is_alive = p1_data.get("is_alive", True)
    player1.facing_left = p1_data.get("facing_left", False) # 新增
    if not player1.is_alive:
        dp_x = p1_data.get("death_pos_x")
        dp_y = p1_data.get("death_pos_y")
        if dp_x is not None and dp_y is not None:
            player1.death_pos = pygame.math.Vector2(dp_x, dp_y)
            player1.original_death_pos_for_shake = pygame.math.Vector2(dp_x, dp_y)
            player1.rect.center = player1.death_pos
            player1._update_dead_image(0) # 設定初始死亡動畫幀
        else: player1.is_alive = True # 若無死亡位置則fallback為存活
    else: player1.death_pos = None
    player1.rect.center = player1.pos


    player2.reset()
    p2_data = load_data.get("player2", {})
    player2.pos = pygame.math.Vector2(p2_data.get("pos_x", player2.start_pos.x), p2_data.get("pos_y", player2.start_pos.y))
    player2.is_alive = p2_data.get("is_alive", True)
    player2.facing_left = p2_data.get("facing_left", False) # 新增
    if not player2.is_alive:
        dp_x = p2_data.get("death_pos_x")
        dp_y = p2_data.get("death_pos_y")
        if dp_x is not None and dp_y is not None:
            player2.death_pos = pygame.math.Vector2(dp_x, dp_y)
            player2.original_death_pos_for_shake = pygame.math.Vector2(dp_x, dp_y)
            player2.rect.center = player2.death_pos
            player2._update_dead_image(0)
        else: player2.is_alive = True
    else: player2.death_pos = None
    player2.rect.center = player2.pos
    player2.can_spawn_item_timer = p2_data.get("can_spawn_item_timer", 0)

    # --- 恢復Boss和可投擲物 (如果是Boss戰) ---
    if game_state == STATE_BOSS_LEVEL:
        boss_data = load_data.get("boss_level_data")
        if boss_data and boss_enemy: # boss_enemy 應由 setup_boss_level() 創建
            boss_enemy.current_health = boss_data.get("boss_current_health", boss_enemy.max_health)
            if boss_enemy.current_health <= 0:
                game_state = STATE_BOSS_DEFEATED
                boss_group.empty()
            else:
                boss_enemy.pos = pygame.math.Vector2(boss_data.get("boss_pos_x", SCREEN_WIDTH // 2), boss_data.get("boss_pos_y", SCREEN_HEIGHT // 4))
                boss_enemy.rect.center = boss_enemy.pos
                boss_enemy.movement_mode = boss_data.get("boss_movement_mode", "simple_four_way")
                boss_enemy.move_timer = boss_data.get("boss_move_timer",0)
                boss_enemy.current_direction = pygame.math.Vector2(boss_data.get("boss_current_direction_x",0), boss_data.get("boss_current_direction_y",0))
                boss_enemy.teleport_timer = boss_data.get("boss_teleport_timer",0)
                boss_enemy.is_teleporting_warning = boss_data.get("boss_is_teleporting_warning", False)
                b_tp_x = boss_data.get("boss_teleport_target_pos_x")
                b_tp_y = boss_data.get("boss_teleport_target_pos_y")
                boss_enemy.teleport_target_pos = pygame.math.Vector2(b_tp_x, b_tp_y) if b_tp_x is not None and b_tp_y is not None else None
                boss_enemy.attack_timer = boss_data.get("boss_attack_timer", 0)
                if boss_enemy not in boss_group: boss_group.add(boss_enemy)

        # 恢復可投擲物
        throwable_objects_group.empty() # 清空 group
        player1.held_object = None # 清空 P1 持有物

        loaded_throwables_data = load_data.get("throwable_objects", [])
        p1_held_object_data_from_save = p1_data.get("held_object_info")

        for obj_data in loaded_throwables_data:
            new_obj = ThrowableObject(obj_data["pos_x"], obj_data["pos_y"], obj_data.get("spawned_by_player_id", 1))
            new_obj.is_thrown = obj_data.get("is_thrown", False)
            new_obj.throw_velocity = pygame.math.Vector2(obj_data.get("throw_velocity_x", 0), obj_data.get("throw_velocity_y", 0))
            throwable_objects_group.add(new_obj)

            # 檢查此物件是否為P1之前持有的物件
            if p1_held_object_data_from_save and \
               obj_data.get("pos_x") == p1_held_object_data_from_save.get("pos_x") and \
               obj_data.get("pos_y") == p1_held_object_data_from_save.get("pos_y") and \
               obj_data.get("spawned_by_player_id") == p1_held_object_data_from_save.get("spawned_by_player_id") and \
               obj_data.get("is_held_by_p1", False): # 使用儲存時的 is_held_by_p1 標記
                player1.held_object = new_obj
                new_obj.pickup(player1.player_id)


    # 確保玩家在正確的 sprite group 中
    player_sprites.empty() # 先清空
    player_sprites.add(player1, player2)

    print("遊戲狀態已載入。")

def draw_leaderboard_screen():
    screen.fill((20, 20, 40))  # 深藍色背景，或者您喜歡的顏色
    title_text = font_large.render("排行榜", True, TEXT_COLOR)
    screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 10))

    if not leaderboard_data:
        no_data_text = font_small.render("尚無紀錄", True, TEXT_COLOR)
        screen.blit(no_data_text, (SCREEN_WIDTH // 2 - no_data_text.get_width() // 2, SCREEN_HEIGHT // 2))
    else:
        start_y = 120  # 排行榜條目開始的 Y 位置
        line_height = LEADERBOARD_FACE_SIZE[1] + 20  # 每條紀錄的高度 (頭像高度 + 間距)
        header_y_offset = -40  # 表頭相對於第一條紀錄的 Y 偏移

        # 設定各欄位的 X 位置
        rank_x = 60
        face_x = rank_x + 70
        name_x = face_x + LEADERBOARD_FACE_SIZE[0] + 25

        # 時間和分數從右邊算回來，確保對齊
        score_col_width = font_small.render("99/99", True, WHITE).get_width() + 10  # 預估分數欄寬度
        time_col_width = font_small.render("99:99.99", True, WHITE).get_width() + 20  # 預估時間欄寬度

        score_x = SCREEN_WIDTH - 70 - score_col_width // 2  # 分數欄中心 X
        time_x = score_x - 30 - time_col_width // 2  # 時間欄中心 X
        max_name_width = time_x - (name_x + font_small.render("...", True, WHITE).get_width()) - 20  # 名字最大寬度

        # 繪製表頭
        headers_info = [
            ("排名", rank_x + font_tiny.render("排名", True, WHITE).get_width() // 2),
            ("頭像", face_x + LEADERBOARD_FACE_SIZE[0] // 2),
            ("名字", name_x + max_name_width // 2),  # 名字表頭大致居中於名字區域
            ("時間", time_x),
            ("分數", score_x)
        ]
        for header_text, hx_center in headers_info:
            header_surf = font_tiny.render(header_text, True, WHITE)
            screen.blit(header_surf, (hx_center - header_surf.get_width() // 2, start_y + header_y_offset))

        for i, entry in enumerate(leaderboard_data):
            if i >= MAX_LEADERBOARD_ENTRIES: break  # 最多顯示 MAX_LEADERBOARD_ENTRIES 筆

            current_entry_y = start_y + i * line_height
            # 計算該行所有文字和圖片的垂直中心點
            y_pos_center_of_row = current_entry_y + LEADERBOARD_FACE_SIZE[1] // 2

            # 1. 排名
            rank_text_surf = font_small.render(f"{i + 1}.", True, TEXT_COLOR)
            screen.blit(rank_text_surf, (rank_x, y_pos_center_of_row - rank_text_surf.get_height() // 2))

            # 2. 頭像
            face_img_surface = None
            img_path = entry.get("face_image_path")  # 從紀錄中取得圖片路徑
            if img_path:  # 如果有路徑
                if img_path in loaded_face_images_cache:  # 檢查快取
                    face_img_surface = loaded_face_images_cache[img_path]
                elif os.path.exists(img_path):  # 如果不在快取中，但檔案存在
                    try:
                        raw_surface = pygame.image.load(img_path).convert_alpha()
                        face_img_surface = pygame.transform.scale(raw_surface, LEADERBOARD_FACE_SIZE)
                        loaded_face_images_cache[img_path] = face_img_surface  # 加入快取
                    except pygame.error as e:
                        print(f"排行榜載入影像錯誤 {img_path}: {e}")
                        face_img_surface = None  # 載入失敗，後面會用預留位置
                # else: 圖片路徑存在於紀錄中，但實際檔案遺失 (後面會用預留位置)

            if face_img_surface is None:  # 如果沒有圖片路徑，或載入失敗
                face_img_surface = pygame.Surface(LEADERBOARD_FACE_SIZE, pygame.SRCALPHA)  # 建立透明的預留位置 Surface
                face_img_surface.fill((60, 60, 70, 180))  # 半透明深灰色
                pygame.draw.rect(face_img_surface, (100, 100, 110),
                                 (0, 0, LEADERBOARD_FACE_SIZE[0], LEADERBOARD_FACE_SIZE[1]), 1)  # 加上邊框
            screen.blit(face_img_surface, (face_x, current_entry_y))  # 繪製頭像 (左上角對齊)

            # 3. 名字 (需要處理過長的名字)
            name_str_original = entry.get("name", "N/A")
            name_text_surf = font_small.render(name_str_original, True, TEXT_COLOR)
            # 如果名字太長，簡單截斷並加上 "..." (更複雜的可以用迴圈逐字元檢查)
            if name_text_surf.get_width() > max_name_width:
                temp_name = ""
                for char_idx in range(len(name_str_original)):
                    temp_name_check = name_str_original[:char_idx + 1] + "..."
                    if font_small.render(temp_name_check, True, TEXT_COLOR).get_width() > max_name_width:
                        name_str_display = name_str_original[:char_idx] + "..."
                        break
                else:  # 如果迴圈正常結束 (名字加上...也不會超長)
                    name_str_display = name_str_original  # 或是 name_str_original[:max_chars_approx] + "..."
                name_text_surf = font_small.render(name_str_display, True, TEXT_COLOR)
            screen.blit(name_text_surf, (name_x, y_pos_center_of_row - name_text_surf.get_height() // 2))

            # 4. 時間
            time_val = entry.get("time", float('inf'))
            time_str_display = "N/A"
            if time_val != float('inf'):
                minutes = int(time_val // 60)
                seconds = int(time_val % 60)
                milliseconds = int((time_val * 100) % 100)  # 取毫秒的前兩位
                time_str_display = f"{minutes:02}:{seconds:02}.{milliseconds:02}"
            time_text_surf = font_small.render(time_str_display, True, TEXT_COLOR)
            screen.blit(time_text_surf, (time_x - time_text_surf.get_width() // 2,
                                         y_pos_center_of_row - time_text_surf.get_height() // 2))  # 文字居中於 time_x

            # 5. 分數
            score_str_display = str(entry.get("score", "0"))
            score_text_surf = font_small.render(score_str_display, True, TEXT_COLOR)
            screen.blit(score_text_surf, (score_x - score_text_surf.get_width() // 2,
                                          y_pos_center_of_row - score_text_surf.get_height() // 2))  # 文字居中於 score_x

    # 繪製「重新開始/離開」的提示
    options_prompt_text_str = "按 R 重新開始 | 按 B 返回主選單 | 按 Q 離開遊戲"
    restart_prompt_surf = font_small.render(options_prompt_text_str, True, TEXT_COLOR)
    screen.blit(restart_prompt_surf, (SCREEN_WIDTH // 2 - restart_prompt_surf.get_width() // 2, SCREEN_HEIGHT - 70))
# ---遊戲初始化---
game_state = STATE_START_SCREEN  #
# current_level_index = 0 # Already defined above
running = True  #

# --- 閃爍文字相關變數 ---
prompt_blink_timer = 0.0  #
prompt_blink_interval = 0.5  #
prompt_text_visible = True  #

# ---復活設置---
REVIVE_HOLD_TIME = 1.5  #
revive_progress = 0.0  #
revive_target = None  #

def draw_game_state_messages():
    global game_time_elapsed, current_score

    if game_state == STATE_GAME_OVER:
        game_over_text = font_large.render("遊戲結束", True, TEXT_COLOR)
        restart_text = font_small.render("按 R 鍵重新開始", True, TEXT_COLOR)
        screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
        screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 20))
    # Removed STATE_PRE_BOSS_COMPLETE message block
    elif game_state == STATE_BOSS_DEFEATED:
        victory_text = font_large.render("Boss 已擊敗！恭喜！", True, (0, 255, 0))
        screen.blit(victory_text, (SCREEN_WIDTH // 2 - victory_text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
        #screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 20))

    if game_state == STATE_PLAYING:
        level_text = font_small.render(f"關卡 {current_level_index + 1}", True, TEXT_COLOR)  #
        screen.blit(level_text, (10, 10))

        # 新增：顯示計時器和分數
        timer_val_str = f"{int(game_time_elapsed // 60):02}:{int(game_time_elapsed % 60):02}"  # 格式化為 MM:SS
        timer_text_surf = font_tiny.render(f"時間: {timer_val_str}", True, TEXT_COLOR)
        screen.blit(timer_text_surf, (SCREEN_WIDTH - timer_text_surf.get_width() - 10, 10))

        score_text_surf = font_tiny.render(f"分數: {current_score}/{MAX_TOTAL_SCORE}", True, TEXT_COLOR)
        screen.blit(score_text_surf, (SCREEN_WIDTH - score_text_surf.get_width() - 10, 35))  # 分數顯示在計時器下方

        p1_status_text = "存活" if player1.is_alive else "死亡";
        p2_status_text = "存活" if player2.is_alive else "死亡"
        p1_text = font_tiny.render(f"玩家1: {p1_status_text}", True, PLAYER1_COLOR);
        screen.blit(p1_text, (10, 50))
        p2_text = font_tiny.render(f"玩家2: {p2_status_text}", True, PLAYER2_COLOR);
        screen.blit(p2_text, (10, 75))
        if (player1.is_alive and not player2.is_alive) or (player2.is_alive and not player1.is_alive):
            revive_hint = font_tiny.render("請 P1 按住'F' / P2 按住'.' 幫隊友復活", True, REVIVE_PROMPT_COLOR)  #
            screen.blit(revive_hint, (SCREEN_WIDTH // 2 - revive_hint.get_width() // 2, 10))
        active_effects = effect_manager.get_active_effects_info()  #
        y_offset = 100
        for effect_str in active_effects:
            effect_surf = font_effect.render(effect_str, True, TEXT_COLOR);
            screen.blit(effect_surf, (10, y_offset));
            y_offset += 20
        if player1.is_alive and player2.is_alive and coop_box_group:
            first_box = next(iter(coop_box_group));
            p1_near = player1.pos.distance_to(first_box.pos) < COOP_BOX_PUSH_RADIUS
            p2_near = player2.pos.distance_to(first_box.pos) < COOP_BOX_PUSH_RADIUS
            if p1_near and p2_near:
                push_hint = font_tiny.render("兩人靠近可推箱", True, (225, 210, 80));
                screen.blit(push_hint, (SCREEN_WIDTH // 2 - push_hint.get_width() // 2, 40))
    elif game_state == STATE_BOSS_LEVEL:
        boss_level_text = font_large.render("!! BOSS BATTLE !!", True, (255, 50, 50))
        screen.blit(boss_level_text, (SCREEN_WIDTH // 2 - boss_level_text.get_width() // 2, 10))

        timer_val_str = f"{int(game_time_elapsed // 60):02}:{int(game_time_elapsed % 60):02}"
        timer_text_surf = font_tiny.render(f"時間: {timer_val_str}", True, TEXT_COLOR)
        screen.blit(timer_text_surf, (SCREEN_WIDTH - timer_text_surf.get_width() - 10, 60))  # 調整 Y 位置

        p1_status_text = "存活" if player1.is_alive else "死亡";
        p2_status_text = "存活" if player2.is_alive else "死亡"
        p1_text = font_tiny.render(f"玩家1: {p1_status_text}", True, PLAYER1_COLOR);
        screen.blit(p1_text, (10, SCREEN_HEIGHT - 80))
        p2_text = font_tiny.render(f"玩家2: {p2_status_text}", True, PLAYER2_COLOR);
        screen.blit(p2_text, (10, SCREEN_HEIGHT - 55))
        if (player1.is_alive and not player2.is_alive) or (player2.is_alive and not player1.is_alive):
            revive_hint = font_tiny.render("請 P1 按住'F' / P2 按住'.' 幫隊友復活", True, REVIVE_PROMPT_COLOR)
            screen.blit(revive_hint, (SCREEN_WIDTH // 2 - revive_hint.get_width() // 2, SCREEN_HEIGHT - 30))

        # P2 Item Cooldown display
        if player2.is_alive and player2.can_spawn_item_timer > 0:
            cd_text = font_effect.render(f"P2 物品CD: {player2.can_spawn_item_timer:.1f}s", True, WHITE)
            screen.blit(cd_text, (SCREEN_WIDTH - cd_text.get_width() - 10, 10))
        elif player2.is_alive:
            cd_text = font_effect.render(f"P2 按 ; 可造物", True, (100, 255, 100))
            screen.blit(cd_text, (SCREEN_WIDTH - cd_text.get_width() - 10, 10))

        # P1 Action Key Hint
        if player1.is_alive:
            action_hint_text = "按 G 拾取"
            if player1.held_object:
                action_hint_text = "按 G 投擲"
            p1_action_hint = font_effect.render(action_hint_text, True, WHITE)
            screen.blit(p1_action_hint, (10, SCREEN_HEIGHT - 100))

# ---遊戲主程式循環---
while running:  #
    dt = clock.tick(FPS) / 1000.0  #
    keys = pygame.key.get_pressed()  #

    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False  #
        if event.type == pygame.USEREVENT + 1:  # Boss color revert timer
            if boss_enemy: boss_enemy.revert_color()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F5:  # 存檔
                save_game_state()
            if event.key == pygame.K_F9:  # 讀檔
                load_game_state_from_file()

        if game_state == STATE_START_SCREEN:  #
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:  #
                    current_level_index = 0;
                    load_level(current_level_index);
                elif event.key == pygame.K_l:  # 'L' 鍵載入遊戲
                    load_game_state_from_file()
                elif event.key == pygame.K_v:  # 按 'V' 查看排行榜
                    load_leaderboard()
                    game_state = STATE_SHOW_LEADERBOARD
                elif event.key == pygame.K_q: # 按 'q' 離開遊戲
                    running = False;

        elif game_state == STATE_BOSS_LEVEL:
            if event.type == pygame.KEYDOWN:
                if event.key == ACTION_KEY_P1:  # P1 action (pickup/throw)
                    player1.handle_action_key(throwable_objects_group)
                elif event.key == DRAW_ITEM_KEY_P2:  # P2 draw item
                    # Spawn near P1. If P1 is dead, spawn at a default location.
                    target_spawn_pos = player1.pos if player1.is_alive else pygame.math.Vector2(ITEM_SPAWN_POS_DEFAULT)
                    player2.handle_draw_item_key(throwable_objects_group, target_spawn_pos)

        elif (game_state == STATE_GAME_OVER or game_state == STATE_BOSS_DEFEATED):  #
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:  #
                current_level_index = 0;
                load_level(current_level_index)  # This resets to level 1

        elif game_state == STATE_ASK_CAMERA:  # 新增：詢問是否使用攝影機
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_y:  # 如果玩家按 'Y' (Yes)
                    game_state = STATE_CAMERA_INPUT
                    player_name_input_active = True  # 開始輸入名稱
                    camera_capture_active = False  # 攝影機尚未啟動
                    photo_taken_prompt_active = False  # 重設拍照後提示狀態
                    current_player_name = ""  # 清空上次的名稱
                    captured_face_image_path = None  # <--- 確保重設
                    current_leaderboard_entry_index = None  # <--- 確保重設
                elif event.key == pygame.K_n:  # 如果玩家按 'N' (No)
                    # 可以選擇在這裡為匿名玩家儲存一筆紀錄 (無照片)
                    # add_leaderboard_entry("Anonymous", final_game_time, final_player_score, None)
                    # save_leaderboard() # 如果有新增紀錄則儲存
                    game_state = STATE_SHOW_LEADERBOARD  # 直接顯示排行榜

        elif game_state == STATE_CAMERA_INPUT:  # 新增：攝影機與名稱輸入
            if player_name_input_active:  # 如果正在輸入名稱
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:  # 按下 Enter 確認名稱
                        if current_player_name.strip():  # 確保名稱不是空白
                            player_name_input_active = False  # 結束名稱輸入
                            captured_face_image_path = None  # <--- 新名字，沒有已拍照片
                            current_leaderboard_entry_index = None  # <--- 新名字，將會是新的排行榜條目
                            initialize_camera_for_capture()  # 嘗試啟動攝影機
                        else:
                            print("提示：玩家名稱不能為空白。")  # 或在遊戲畫面顯示提示
                    elif event.key == pygame.K_BACKSPACE:  # 按下 Backspace 刪除字元
                        current_player_name = current_player_name[:-1]
                    # 只允許輸入英文字母、數字和空白 (或者更嚴格的英文名)
                    elif event.unicode.isprintable() and (
                            event.unicode.encode('utf-8').isalpha() or event.unicode.isdigit() or event.unicode == ' '):
                        if len(current_player_name) < 20:  # 限制名稱長度
                            current_player_name += event.unicode

            elif camera_capture_active and not photo_taken_prompt_active:  # 如果攝影機已啟動且尚未進入拍照後提示
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_a:  # 按 'A' 拍照
                        handle_photo_capture()  # 拍照成功會設定 photo_taken_prompt_active = True
                    elif event.key == pygame.K_q:  # 按 'Q' 跳過此次拍照/紀錄
                        release_camera_resources()
                        save_leaderboard()  # 如果之前有拍過照並add_entry，這裡儲存
                        current_player_name = ""
                        captured_face_image_path = None
                        current_leaderboard_entry_index = None
                        game_state = STATE_SHOW_LEADERBOARD

            elif photo_taken_prompt_active:  # 如果已拍完照，顯示後續選項
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_c:  # (C)apture another: 用同一個名字再拍一張 (會覆蓋或產生新索引檔)
                        photo_taken_prompt_active = False  # 清除提示，回到拍照模式
                        if not cap or not cap.isOpened():  # 確保攝影機仍然可用
                            initialize_camera_for_capture()
                        # 攝影機應該仍然是啟動的
                    elif event.key == pygame.K_n:  # (N)ew name: 換一個名字拍照 (等於開始一筆新的排行榜紀錄)
                        photo_taken_prompt_active = False
                        player_name_input_active = True  # 回到名稱輸入模式
                        current_player_name = ""  # 清空目前名稱
                        captured_face_image_path = None  # <--- 為新名字重設
                        current_leaderboard_entry_index = None  # <--- 新名字將是新的排行榜條目
                        if not cap or not cap.isOpened():  # 確保攝影機是開啟的
                            initialize_camera_for_capture()
                    elif event.key == pygame.K_d:  # (D)one: 完成所有拍照
                        photo_taken_prompt_active = False
                        release_camera_resources()  # 釋放攝影機
                        save_leaderboard()  # 儲存所有已加入的排行榜紀錄
                        current_player_name = ""
                        captured_face_image_path = None
                        current_leaderboard_entry_index = None
                        game_state = STATE_SHOW_LEADERBOARD  # 前往排行榜

        elif game_state == STATE_SHOW_LEADERBOARD:  # 新增：顯示排行榜時的事件
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:  # 按 'R' 重新開始遊戲
                    current_level_index = 0
                    game_time_elapsed = 0.0  # 重設遊戲時間
                    current_score = 0  # 重設分數
                    load_leaderboard()  # 重新載入排行榜

                    current_player_name = ""
                    captured_face_image_path = None
                    current_leaderboard_entry_index = None
                    player_name_input_active = False  # 確保輸入旗標也重設
                    camera_capture_active = False  # 確保攝影機狀態重設
                    photo_taken_prompt_active = False

                    load_level(current_level_index)  # 開始第一關
                elif event.key == pygame.K_q:  # 按 'Q' 離開遊戲
                    running = False
                elif event.key == pygame.K_b:  # 按 'B' 返回開始畫面
                    game_state = STATE_START_SCREEN
                    prompt_blink_timer = 0.0
                    prompt_text_visible = True

    if game_state == STATE_START_SCREEN:  #
        prompt_blink_timer += dt  #
        if prompt_blink_timer >= prompt_blink_interval:
            prompt_blink_timer = 0.0;
            prompt_text_visible = not prompt_text_visible  #

    elif game_state == STATE_PLAYING:
        game_time_elapsed += dt
        effect_manager.update(dt)
        player1.update_movement(laser_wall_sprites, coop_box_group, spike_trap_group, meteor_sprites, effect_manager, dt)
        player2.update_movement(laser_wall_sprites, coop_box_group, spike_trap_group, meteor_sprites, effect_manager, dt)

        for player in player_sprites: # 處理玩家與果實的碰撞
            if player.is_alive:
                collided_fruits = pygame.sprite.spritecollide(player, fruit_sprites, True)
                for fruit in collided_fruits:
                    if fruit.fruit_type == "score":
                        if current_score < MAX_TOTAL_SCORE:
                            current_score += SCORE_FRUIT_VALUE
                    else:
                        effect_manager.apply_effect(fruit.fruit_type, player.player_id)

        if effect_manager.should_spawn_meteor():  #
            spawn_x = random.randint(METEOR_SIZE, SCREEN_WIDTH - METEOR_SIZE);
            spawn_y = random.randint(METEOR_SIZE, SCREEN_HEIGHT - METEOR_SIZE)  #
            warning_sprites.add(Warning(spawn_x, spawn_y, METEOR_WARNING_TIME));
            effect_manager.reset_meteor_timer()  #
        for warning in list(warning_sprites):  #
            if warning.update(dt): meteor_sprites.add(Meteor(warning.spawn_pos[0], warning.spawn_pos[1]))  #
        warning_sprites.update(dt);
        meteor_sprites.update(dt)  #

        if player1.is_alive and player2.is_alive:  #
            for coop_box in coop_box_group:  #
                p1_near = player1.pos.distance_to(coop_box.pos) < COOP_BOX_PUSH_RADIUS;
                p2_near = player2.pos.distance_to(coop_box.pos) < COOP_BOX_PUSH_RADIUS  #
                if p1_near and p2_near:  #
                    total_dir = pygame.math.Vector2(0, 0)
                    if keys[player1.control_keys['right']]: total_dir.x += 1;  #
                    if keys[player1.control_keys['left']]: total_dir.x -= 1  #
                    if keys[player1.control_keys['down']]: total_dir.y += 1  #
                    if keys[player1.control_keys['up']]: total_dir.y -= 1  #
                    if keys[player2.control_keys['right']]: total_dir.x += 1  #
                    if keys[player2.control_keys['left']]: total_dir.x -= 1  #
                    if keys[player2.control_keys['down']]: total_dir.y += 1  #
                    if keys[player2.control_keys['up']]: total_dir.y -= 1  #
                    if total_dir.length_squared() > 0: total_dir.normalize_ip(); coop_box.move(total_dir,
                                                                                               laser_wall_sprites)  #
        # Chain Physics (Copied from original)
        for _ in range(CHAIN_ITERATIONS):  #
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

        goal1.update_status(player1);
        goal2.update_status(player2)  #
        if goal1.is_active and goal2.is_active and player1.is_alive and player2.is_alive:  #
            current_level_index += 1  #
            load_level(current_level_index) # This will call setup_boss_level() if all regular levels are done
        if not player1.is_alive and not player2.is_alive: game_state = STATE_GAME_OVER  #

    elif game_state == STATE_BOSS_LEVEL:
        game_time_elapsed += dt

        player1.update_movement(None, None, None, None, effect_manager, dt, boss_enemy, boss_enemy.projectiles, throwable_objects_group)
        player2.update_movement(None, None, None, None, effect_manager, dt, boss_enemy, boss_enemy.projectiles, throwable_objects_group)
        player1.update_boss_interactions(dt)
        player2.update_boss_interactions(dt)

        if boss_enemy:
            boss_enemy.update(dt, player_sprites, SCREEN_WIDTH, SCREEN_HEIGHT)
            # Check for P1's thrown object hitting boss
            for obj in throwable_objects_group:
                if obj.is_thrown and boss_enemy.rect.colliderect(obj.rect):
                    boss_enemy.take_damage(obj.damage)
                    obj.kill()  # Remove object after hitting
                    if boss_enemy.current_health <= 0:
                        game_state = STATE_BOSS_DEFEATED
                        boss_group.empty()  # Remove boss
                        throwable_objects_group.empty()  # Clear remaining items
                        if boss_enemy: boss_enemy.projectiles.empty()  # Clear projectiles
                        break  # Exit loop as boss is defeated
            if boss_enemy.current_health <= 0:  # Double check if boss was defeated
                final_game_time = game_time_elapsed
                final_player_score = current_score

                boss_group.empty()
                throwable_objects_group.empty()
                if boss_enemy and hasattr(boss_enemy, 'projectiles'): boss_enemy.projectiles.empty()

                game_state = STATE_ASK_CAMERA
            elif not player1.is_alive and not player2.is_alive:
                game_state = STATE_GAME_OVER  # Both players died during boss fight

        throwable_objects_group.update(dt)  # Update all throwable items (gravity if thrown, etc.)
        # Ensure held items are also updated if their update logic needs it separate from player
        if player1.held_object: player1.held_object.update(dt, player1.pos, player1.facing_left)
        # Chain physics for boss level (same logic, just no coop boxes etc.)
        for _ in range(CHAIN_ITERATIONS):
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

    elif game_state == STATE_CAMERA_INPUT:
        if camera_capture_active and not player_name_input_active and not photo_taken_prompt_active:
            process_camera_frame()  # Update camera_frame_surface for display

    # ---遊戲畫面繪製---
    screen.fill(BLACK)  #

    if game_state == STATE_START_SCREEN:  #
        title_text = font_large.render("雙人合作遊戲 Demo", True, TEXT_COLOR);
        screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, SCREEN_HEIGHT // 3))  #
        if prompt_text_visible:
            start_prompt_text = font_small.render("按 Enter 開始遊戲", True, TEXT_COLOR);
            screen.blit(start_prompt_text,(SCREEN_WIDTH // 2 - start_prompt_text.get_width() // 2,SCREEN_HEIGHT // 2))
            load_prompt_text = font_small.render("按 L 載入遊戲", True, TEXT_COLOR)  # 新增提示
            screen.blit(load_prompt_text, (SCREEN_WIDTH // 2 - load_prompt_text.get_width() // 2, SCREEN_HEIGHT // 2 + 40))
            view_leaderboard_prompt_text = font_small.render("按 V 查看排行榜", True, TEXT_COLOR)
            screen.blit(view_leaderboard_prompt_text,(SCREEN_WIDTH // 2 - view_leaderboard_prompt_text.get_width() // 2, SCREEN_HEIGHT // 2 + 80))
            quit_prompt_text = font_small.render("按 Q 退出遊戲", True, TEXT_COLOR)
            screen.blit(quit_prompt_text,(SCREEN_WIDTH // 2 - quit_prompt_text.get_width() // 2, SCREEN_HEIGHT // 2 + 120))

    elif game_state == STATE_PLAYING:  #
        current_lw_alpha = effect_manager.get_laser_wall_alpha()  #
        for wall_sprite in laser_wall_sprites:  #
            if hasattr(wall_sprite, 'update_visuals'): wall_sprite.update_visuals(current_lw_alpha)  #
        laser_wall_sprites.draw(screen)  #
        goal_sprites.draw(screen)  #
        for goal_sprite in goal_sprites: goal_sprite.draw(screen)  #
        for coop_box_item in coop_box_group: coop_box_item.draw(screen)  #
        # Number display on boxes
        # ... (rest of coop box number display logic from original)
        for spike in spike_trap_group: spike.update(dt); spike.draw(screen)  #
        fruit_sprites.draw(screen);
        warning_sprites.draw(screen);
        meteor_sprites.draw(screen)  #

    elif game_state == STATE_BOSS_LEVEL:
        # Draw boss, its projectiles, and throwable objects
        if boss_enemy:
            boss_enemy.draw(screen)  # Boss also draws its projectiles
        throwable_objects_group.draw(screen)
        # Draw P1's held object separately if it's removed from group when held
        if player1.held_object:
            player1.held_object.draw(screen)

    # Draw players and chain (common to PLAYING and BOSS_LEVEL)
    if game_state == STATE_PLAYING or game_state == STATE_BOSS_LEVEL:
        chain_start_pos = None;
        chain_end_pos = None;
        can_draw_chain = False  #
        if player1.is_alive and player2.is_alive:
            chain_start_pos = player1.rect.center; chain_end_pos = player2.rect.center; can_draw_chain = True  #
        elif player1.is_alive and not player2.is_alive and player2.death_pos:
            chain_start_pos = player1.rect.center; chain_end_pos = player2.death_pos; can_draw_chain = True  #
        elif player2.is_alive and not player1.is_alive and player1.death_pos:
            chain_start_pos = player2.rect.center; chain_end_pos = player1.death_pos; can_draw_chain = True  #
        if can_draw_chain: pygame.draw.line(screen, CHAIN_COLOR, chain_start_pos, chain_end_pos, 3)  #
        player_sprites.draw(screen)  #

    # Draw UI messages (common to most states or handled within)
    draw_game_state_messages()  #
    # 新增：新遊戲狀態的繪製邏輯
    if game_state == STATE_ASK_CAMERA:
        ask_text = font_small.render("啟用攝影機擷取頭像? (Y / N)", True, TEXT_COLOR)
        screen.blit(ask_text, (SCREEN_WIDTH // 2 - ask_text.get_width() // 2, SCREEN_HEIGHT // 2 - 20))

    elif game_state == STATE_CAMERA_INPUT:
        if player_name_input_active:  # 如果正在輸入名稱
            name_prompt_text = font_small.render("請輸入英文名字 (Enter 確認):", True, TEXT_COLOR)
            screen.blit(name_prompt_text,
                        (SCREEN_WIDTH // 2 - name_prompt_text.get_width() // 2, SCREEN_HEIGHT // 2 - 100))

            # 繪製名稱輸入框
            name_field_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 60, 300, 40)
            pygame.draw.rect(screen, WHITE, name_field_rect, 2)  # 框線
            name_input_surf = font_small.render(current_player_name, True, WHITE)  # 目前輸入的文字
            screen.blit(name_input_surf, (name_field_rect.x + 5, name_field_rect.y + (
                        name_field_rect.height - name_input_surf.get_height()) // 2))  # 文字垂直居中

            # (選擇性) 繪製閃爍的游標
            if pygame.time.get_ticks() % 1000 < 500:  # 每 0.5 秒閃爍一次
                cursor_x = name_field_rect.x + 5 + name_input_surf.get_width()
                if cursor_x < name_field_rect.right - 5:  # 確保游標在框內
                    pygame.draw.line(screen, WHITE, (cursor_x, name_field_rect.y + 5),
                                     (cursor_x, name_field_rect.y + name_field_rect.height - 5), 2)

        elif camera_capture_active and not photo_taken_prompt_active:  # 如果攝影機啟動且不是在拍照後提示階段
            if camera_frame_surface:  # 如果 Pygame 的攝影機畫面 Surface 已準備好
                # 計算攝影機畫面的顯示位置 (例如，居中，上方留空間給標題)
                feed_x = (SCREEN_WIDTH - camera_frame_surface.get_width()) // 2
                feed_y = (SCREEN_HEIGHT - camera_frame_surface.get_height()) // 2 - 80  # 向上移動一些
                screen.blit(camera_frame_surface, (feed_x, feed_y))
            else:  # 如果畫面還沒準備好 (例如，攝影機剛啟動)
                init_cam_text = font_small.render("正在初始化攝影機...", True, TEXT_COLOR)
                screen.blit(init_cam_text,
                            (SCREEN_WIDTH // 2 - init_cam_text.get_width() // 2, SCREEN_HEIGHT // 2 - 20))

            capture_prompt_text_str = "將臉對準框内, 按 'A' 拍照, 按 'Q' 跳過此次紀錄"
            capture_prompt_surf = font_tiny.render(capture_prompt_text_str, True, TEXT_COLOR)
            screen.blit(capture_prompt_surf,
                        (SCREEN_WIDTH // 2 - capture_prompt_surf.get_width() // 2, SCREEN_HEIGHT - 70))

        elif photo_taken_prompt_active:  # 如果已拍照，顯示後續操作提示
            # (選擇性) 繼續顯示攝影機畫面作為背景
            if camera_capture_active and camera_frame_surface:
                feed_x = (SCREEN_WIDTH - camera_frame_surface.get_width()) // 2
                feed_y = (SCREEN_HEIGHT - camera_frame_surface.get_height()) // 2 - 120  # 再向上移動一些
                screen.blit(camera_frame_surface, (feed_x, feed_y))

            prompt_base_y = SCREEN_HEIGHT - 100
            success_text_surf = font_small.render("照片已儲存!", True, (0, 255, 0))  # 綠色表示成功
            screen.blit(success_text_surf, (SCREEN_WIDTH // 2 - success_text_surf.get_width() // 2, prompt_base_y - 40))

            options_text_str = "重拍一張(C) | 換名字並重拍(N) | 完成並查看排行榜(D)"
            options_text_surf = font_tiny.render(options_text_str, True, TEXT_COLOR)
            screen.blit(options_text_surf, (SCREEN_WIDTH // 2 - options_text_surf.get_width() // 2, prompt_base_y))

    elif game_state == STATE_SHOW_LEADERBOARD:  # 新增：顯示排行榜
        draw_leaderboard_screen()

    show_opencv_paint_window()  #

    # --- 復活邏輯 (Common to PLAYING and BOSS_LEVEL) ---
    if game_state == STATE_PLAYING or game_state == STATE_BOSS_LEVEL:
        current_revive_initiator = None;
        potential_target_player = None  #
        if player1.is_alive and not player2.is_alive and player2.death_pos:  #
            if player1.pos.distance_to(player2.death_pos) <= REVIVAL_RADIUS:  #
                if keys[REVIVE_KEYP1]: current_revive_initiator = player1; potential_target_player = player2;  #
        elif player2.is_alive and not player1.is_alive and player1.death_pos:  #
            if player2.pos.distance_to(player1.death_pos) <= REVIVAL_RADIUS:  #
                if keys[REVIVE_KEYP2]: current_revive_initiator = player2; potential_target_player = player1;  #

        if current_revive_initiator and potential_target_player:
            if revive_target != potential_target_player: revive_target = potential_target_player; revive_progress = 0  #
            revive_progress += dt  #
        else:  # No active attempt or conditions not met
            # Only reset progress if the key for the current target is NOT being pressed OR if distance is too great
            reset_progress_flag = True
            if revive_target == player2 and keys[
                REVIVE_KEYP1] and player1.is_alive and player2.death_pos and player1.pos.distance_to(
                    player2.death_pos) <= REVIVAL_RADIUS:
                reset_progress_flag = False
            if revive_target == player1 and keys[
                REVIVE_KEYP2] and player2.is_alive and player1.death_pos and player2.pos.distance_to(
                    player1.death_pos) <= REVIVAL_RADIUS:
                reset_progress_flag = False

            if reset_progress_flag:
                revive_progress = 0  #
                # revive_target = None # Optionally reset target too if key is fully released / conditions fail

        if revive_progress >= REVIVE_HOLD_TIME and revive_target is not None:  #
            if revive_target == player2:
                player2.revive()  #
            elif revive_target == player1:
                player1.revive()  #
            revive_progress = 0;
            revive_target = None  #

        # --- 繪製復活進度圈 ---
        if revive_target is not None and revive_progress > 0:  #
            percentage = min(revive_progress / REVIVE_HOLD_TIME, 1.0);
            center_pos_death = None  #
            if revive_target == player1 and player1.death_pos:
                center_pos_death = player1.death_pos  #
            elif revive_target == player2 and player2.death_pos:
                center_pos_death = player2.death_pos  #
            if center_pos_death:
                radius = 20;
                arc_rect = pygame.Rect(int(center_pos_death.x) - radius,
                                       int(center_pos_death.y - PLAYER_RADIUS - radius * 1.5) - radius, radius * 2,
                                       radius * 2)  #
                pygame.draw.circle(screen, (80, 80, 80, 150) if pygame.SRCALPHA else (80, 80, 80), arc_rect.center,
                                   radius, 2)  #
                start_angle_rad = -math.pi / 2;
                end_angle_rad = start_angle_rad + (percentage * 2 * math.pi)  #
                if percentage > 0.01: pygame.draw.arc(screen, REVIVE_PROMPT_COLOR, arc_rect, start_angle_rad,
                                                      end_angle_rad, 4)  #

    pygame.display.flip()  #

release_camera_resources()
pygame.quit()