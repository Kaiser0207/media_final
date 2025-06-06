import math

import pygame
import random
from animations import *

SCREEN_WIDTH = 1080
SCREEN_HEIGHT = 720
PLAYER_RADIUS = 15 # Used for scaling throwable, can be adjusted

# --- Boss Class ---
class Boss(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # 加载运行动画帧
        self.run_animation_frames = boss_animation.load_boos_run_animation(200, 200)
        self.run2_animation_frames = None  # For phase 2 animation
        self.phase2_animation_switched = False  # To ensure switch happens once
        self.current_frame_index = 0
        self.animation_timer = 0
        self.animation_speed = 0.129  # 每帧持续时间（秒）

        self.image = self.run_animation_frames[self.current_frame_index]  # 初始帧
        self.rect = self.image.get_rect(center=(x, y))
        self.pos = pygame.math.Vector2(x, y)
        self.max_health = 100
        self.current_health = self.max_health
        self.speed = 2
        self.movement_mode = "simple_four_way" # "simple_four_way", "teleport"
        self.move_timer = 0
        self.move_duration = random.uniform(1, 3)
        self.current_direction = pygame.math.Vector2(0,0)
        self.teleport_timer = 0
        self.teleport_cooldown = 5 # Seconds
        self.teleport_warning_duration = 1 # Seconds
        self.is_teleporting_warning = False
        self.teleport_target_pos = None

        self.attack_timer = 0
        self.attack_cooldown = 2 # Seconds
        self.projectiles = pygame.sprite.Group()
        self.font = pygame.font.Font(None, 24)

    def update(self, dt, players_group, screen_width, screen_height):
        # --- Movement ---
        # Switch to phase 2 animation if health <= 50
        if self.current_health <= self.max_health / 2 and not self.phase2_animation_switched:
            if self.run2_animation_frames is None:
                self.run2_animation_frames = boss_animation.load_boos_run2_animation(200, 200)
            self.run_animation_frames = self.run2_animation_frames
            self.animation_speed = 0.08
            self.phase2_animation_switched = True

        if self.current_health <= self.max_health / 2 and self.movement_mode == "simple_four_way":
            self.movement_mode = "teleport" # Switch to teleport below half health
            self.teleport_timer = self.teleport_cooldown # Allow immediate first teleport

        if self.movement_mode == "simple_four_way":
            self.move_timer += dt
            if self.move_timer >= self.move_duration:
                self.move_timer = 0
                self.move_duration = random.uniform(1, 2.5)
                # Choose a random cardinal direction
                directions = [pygame.math.Vector2(1,0), pygame.math.Vector2(-1,0),
                              pygame.math.Vector2(0,1), pygame.math.Vector2(0,-1)]
                self.current_direction = random.choice(directions)

            self.pos += self.current_direction * self.speed
            # Boundary check
            self.pos.x = max(self.rect.width // 2, min(self.pos.x, screen_width - self.rect.width // 2))
            self.pos.y = max(self.rect.height // 2, min(self.pos.y, screen_height - self.rect.height // 2))
            self.rect.center = self.pos

            # 更新动画帧
            self.animation_timer += dt
            if self.animation_timer >= self.animation_speed:
                self.animation_timer = 0
                self.current_frame_index = (self.current_frame_index + 1) % len(self.run_animation_frames)
                frame = self.run_animation_frames[self.current_frame_index]
                # 判断是否向左移动
                if self.current_direction.x < 0:
                    self.image = pygame.transform.flip(frame, True, False)
                else:
                    self.image = frame

        elif self.movement_mode == "teleport":
            self.teleport_timer += dt
            # 播放奔跑动画（血量小于50时也播放奔跑动画）
            self.animation_timer += dt
            if self.animation_timer >= self.animation_speed:
                self.animation_timer = 0
                self.current_frame_index = (self.current_frame_index + 1) % len(self.run_animation_frames)
                frame = self.run_animation_frames[self.current_frame_index]
                # 判断是否向左移动
                if self.current_direction.x < 0:
                    self.image = pygame.transform.flip(frame, True, False)
                else:
                    self.image = frame
            if self.is_teleporting_warning:
                if self.teleport_timer >= self.teleport_warning_duration:
                    self.is_teleporting_warning = False
                    self.teleport_timer = 0 # Reset timer for cooldown
                    if self.teleport_target_pos:
                        self.pos = self.teleport_target_pos
                        self.rect.center = self.pos
                    self.image.set_alpha(255) # Become visible
            elif self.teleport_timer >= self.teleport_cooldown:
                self.teleport_timer = 0 # Reset timer for warning
                self.is_teleporting_warning = True
                self.teleport_target_pos = pygame.math.Vector2(
                    random.randint(self.rect.width // 2, screen_width - self.rect.width // 2),
                    random.randint(self.rect.height // 2, screen_height - self.rect.height // 2)
                )
                self.image.set_alpha(100) # Semi-transparent during warning


        # --- Attack ---
        self.attack_timer += dt
        if self.attack_timer >= self.attack_cooldown:
            self.attack_timer = 0
            self.attack()
            if self.movement_mode == "teleport": # Faster attacks in teleport mode
                self.attack_cooldown = random.uniform(0.8, 1.5)
            else:
                self.attack_cooldown = random.uniform(1.5, 2.5)


        self.projectiles.update(dt)

    def attack(self):
        # Throw projectiles in 4 or 8 directions
        directions = [
            pygame.math.Vector2(1, 0), pygame.math.Vector2(-1, 0),
            pygame.math.Vector2(0, 1), pygame.math.Vector2(0, -1),
            pygame.math.Vector2(1, 1).normalize(), pygame.math.Vector2(1, -1).normalize(),
            pygame.math.Vector2(-1, 1).normalize(), pygame.math.Vector2(-1, -1).normalize()
        ]
        for direction in random.sample(directions, random.randint(4,8)): # Random number of projectiles
            proj = BossProjectile(self.rect.centerx, self.rect.centery, direction)
            self.projectiles.add(proj)

    def take_damage(self, amount):
        self.current_health -= amount
        self.current_health = max(0, self.current_health)
        # Removed visual feedback for damage

    def revert_color(self):
        self.image.fill((200, 0, 0))

    def draw_health_bar(self, surface):
        bar_width = 100
        bar_height = 10
        health_percentage = self.current_health / self.max_health
        current_bar_width = int(bar_width * health_percentage)

        bar_x = self.rect.centerx - bar_width // 2
        bar_y = self.rect.top - bar_height - 5

        pygame.draw.rect(surface, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height)) # Background
        pygame.draw.rect(surface, (0, 200, 0), (bar_x, bar_y, current_bar_width, bar_height)) # Health
        pygame.draw.rect(surface, (255,255,255), (bar_x, bar_y, bar_width, bar_height),1) # Border

        # Health text
        # health_text_surf = self.font.render(f"{self.current_health}/{self.max_health}", True, (255,255,255))
        # surface.blit(health_text_surf, (bar_x + bar_width + 5, bar_y))


    def draw(self, surface):
        if self.is_teleporting_warning and self.teleport_target_pos:
             # Draw a warning marker at the target teleport location
            pygame.draw.circle(surface, (255, 255, 0, 150), self.teleport_target_pos, self.rect.width // 2, 5)

        surface.blit(self.image, self.rect)
        self.projectiles.draw(surface)
        self.draw_health_bar(surface)


class BossProjectile(pygame.sprite.Sprite):
    def __init__(self, x, y, direction_vector):
        super().__init__()
        self.image = pygame.Surface([15, 15])
        self.image.fill((255, 120, 0)) # Orange projectile
        pygame.draw.circle(self.image, (255,0,0), (7,7), 7) # Smaller red circle
        self.rect = self.image.get_rect(center=(x,y))
        self.pos = pygame.math.Vector2(x,y)
        self.speed = 4
        self.direction = direction_vector.normalize()
        self.lifetime = 7 # seconds
        self.timer = 0

    def update(self, dt):
        self.pos += self.direction * self.speed
        self.rect.center = self.pos
        self.timer += dt
        if self.timer > self.lifetime:
            self.kill() # Remove if off-screen or lifetime expires
        if not (0 < self.rect.centerx < SCREEN_WIDTH and 0 < self.rect.centery < SCREEN_HEIGHT):
            self.kill()

class ThrowableObject(pygame.sprite.Sprite):
    def __init__(self, x, y, spawned_by_player_id,detected_shape):
        super().__init__()
        self.original_image = pygame.Surface([PLAYER_RADIUS * 1.8, PLAYER_RADIUS * 1.8]) # Slightly smaller than player
        if spawned_by_player_id == 1: # P2 (Witch) spawns it
            print(detected_shape)
            object_size = PLAYER_RADIUS * 1.8
            fill_color = (150, 50, 200)  # 紫色
            border_color = (200, 100, 250)  # 淺紫色邊框
            # 繪製形狀
            if detected_shape == "Circle":
                # 圓形
                radius = object_size // 2
                pygame.draw.circle(self.original_image, fill_color, (object_size // 2, object_size // 2), radius)
                # 圓形通常不需要額外的邊框，但如果需要可以再畫一個
                pygame.draw.circle(self.original_image, border_color, (object_size // 2, object_size // 2), radius, 3)
            elif detected_shape == "Triangle":
                # 三角形 (等邊三角形)
                # 計算頂點位置
                height = object_size * (math.sqrt(3) / 2)  # 等邊三角形高
                points = [
                    (object_size // 2, object_size - height),  # 頂點
                    (0, object_size),  # 左下角
                    (object_size, object_size)  # 右下角
                ]
                pygame.draw.polygon(self.original_image, fill_color, points)
                pygame.draw.polygon(self.original_image, border_color, points, 3)  # 邊框
            elif detected_shape == "Rectangle":  # 預設為矩形，或當形狀名稱不匹配時
                # 矩形
                self.original_image.fill(fill_color)
                pygame.draw.rect(self.original_image, border_color, self.original_image.get_rect(), 3)
        else: # Default or P1 related (though P1 doesn't spawn)
            self.original_image.fill((100, 100, 100)) # Grey

        self.image = self.original_image.copy()
        self.rect = self.image.get_rect(center=(x,y))
        self.pos = pygame.math.Vector2(x,y)
        self.is_held = False
        self.held_by_player_id = None
        self.throw_velocity = pygame.math.Vector2(0,0)
        self.is_thrown = False
        self.damage = 50 # Damage this object does to the boss
        self.throw_gravity = 0.2 # A little drop when thrown
        self.throw_speed = 10

    def update(self, dt, held_pos=None, facing_left=False):
        if self.is_held and held_pos:
            self.pos = pygame.math.Vector2(held_pos)
            # Position slightly in front of player based on facing direction
            offset = PLAYER_RADIUS * 1.5
            if facing_left:
                self.pos.x -= offset
            else:
                self.pos.x += offset
            self.rect.center = self.pos
        elif self.is_thrown:
            self.throw_velocity.y += self.throw_gravity # Apply gravity
            self.pos += self.throw_velocity * dt * 60 # Scale by 60 assuming dt is 1/60
            self.rect.center = self.pos
            # Remove if off-screen
            if not ( -self.rect.width < self.rect.centerx < SCREEN_WIDTH + self.rect.width and \
                     -self.rect.height < self.rect.centery < SCREEN_HEIGHT + self.rect.height):
                self.kill()


    def pickup(self, player_id):
        self.is_held = True
        self.is_thrown = False
        self.throw_velocity = pygame.math.Vector2(0,0)
        self.held_by_player_id = player_id

    def throw(self, direction_vector):
        self.is_held = False
        self.is_thrown = True
        self.throw_velocity = direction_vector.normalize() * self.throw_speed
        self.held_by_player_id = None

    def draw(self, surface):
        surface.blit(self.image, self.rect)

