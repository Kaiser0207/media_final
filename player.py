import pygame
from animations import *
# 如有需要，导入 math、random 及 main.py 里用到的常量
import random

SCREEN_WIDTH = 1080
SCREEN_HEIGHT = 720
PLAYER_RADIUS = 15
PLAYER_SPEED = 3
FPS = 60


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, alive_color, dead_color, control_keys, player_id):
        super().__init__()
        self.start_pos = pygame.math.Vector2(x, y)
        self.pos = pygame.math.Vector2(x, y)
        self.alive_color = alive_color
        self.dead_color = dead_color
        self.control_keys = control_keys
        self.player_id = player_id
        self.facing_left = False
        self.walk_frames = []
        self.idle_frames = []
        self.death_frames = []

        if self.player_id == 0:
            self.walk_frames = load_knight_run_animation(target_width=PLAYER_RADIUS * 3,
                                                         target_height=PLAYER_RADIUS * 3)
            self.idle_frames = load_knight_idle_animation(target_width=PLAYER_RADIUS * 3,
                                                          target_height=PLAYER_RADIUS * 3)
            self.death_frames = load_knight_death_animation(target_width=PLAYER_RADIUS * 3,
                                                            target_height=PLAYER_RADIUS * 3)
            self.revive_frames = load_knight_revive_animation(target_width=PLAYER_RADIUS * 3,
                                                              target_height=PLAYER_RADIUS * 3)
            self.is_witch = False
        elif self.player_id == 1:
            self.is_witch = True
            self.walk_frames = load_witch_run_animation(target_width=PLAYER_RADIUS * 3,
                                                        target_height=PLAYER_RADIUS * 3)
            self.idle_frames = load_witch_idle_animation(target_width=PLAYER_RADIUS * 3,
                                                         target_height=PLAYER_RADIUS * 3)
            self.death_frames = load_witch_death_animation(target_width=PLAYER_RADIUS * 3,
                                                           target_height=PLAYER_RADIUS * 3)
            self.revive_frames = load_witch_revive_animation(target_width=PLAYER_RADIUS * 3,
                                                             target_height=PLAYER_RADIUS * 3)

        self.frame_interval = 0.2
        self.idle_frame_interval = 0.3

        self.dead_frames = []
        for frame in self.walk_frames:
            dead_frame = frame.copy()
            dead_frame.set_alpha(100)
            self.dead_frames.append(dead_frame)

        self.current_frame = 0
        self.frame_timer = 0
        self.image = self.walk_frames[0]
        self.rect = self.image.get_rect(center=self.pos)
        self.is_alive = True
        self.death_pos = None
        self.is_shaking = False
        self.shake_timer = 0.0
        self.shake_duration = 0.2
        self.shake_magnitude = 4
        self.original_death_pos_for_shake = None
        self.is_reviving = False
        self.revive_anim_timer = 0.0
        self.revive_anim_frame = 0

    def reset(self):
        self.pos = pygame.math.Vector2(self.start_pos.x, self.start_pos.y)
        self.is_alive = True
        self.death_pos = None
        self.image = self.walk_frames[0]
        self.rect = self.image.get_rect(center=self.pos)
        self.current_frame = 0

        # Reset shake attributes
        self.is_shaking = False
        self.shake_timer = 0.0
        self.original_death_pos_for_shake = None
        self.is_reviving = False
        self.revive_anim_timer = 0.0
        self.revive_anim_frame = 0

    def revive(self):
        self.is_alive = True
        if self.death_pos:
            self.pos = pygame.math.Vector2(self.death_pos.x, self.death_pos.y)  # Revive at final death position
        else:  # Fallback if revived without a specific death_pos (e.g. game reset)
            self.pos = pygame.math.Vector2(self.start_pos.x, self.start_pos.y)

        self.rect.center = self.pos
        # 啟動復活動畫
        self.is_reviving = True
        self.revive_anim_timer = 0.0
        self.revive_anim_frame = 0
        self.current_frame = 0  # Reset animation frame

        self.is_shaking = False  # Crucial: stop shaking if revived
        self.shake_timer = 0.0
        self.original_death_pos_for_shake = None  # Clear shake-related temp state
        self.death_pos = None  # Player is no longer considered "at a death position"

    def die(self):
        if self.is_alive:
            self.is_alive = False
            if not self.is_shaking and self.death_pos is None:
                self.death_pos = pygame.math.Vector2(self.pos.x, self.pos.y)
                self.current_frame = 0
                self.frame_timer = 0
                self.is_shaking = False
                self.shake_timer = 0.0
                self.original_death_pos_for_shake = pygame.math.Vector2(self.pos.x, self.pos.y)

    # MODIFIED: update_movement to integrate fruit effects
    def update_movement(self, laser_walls, coop_boxes=None, spike_trap_group=None, meteor_sprites=None,
                        effect_manager=None, dt=0.016):
        # 復活動畫播放時，僅播放動畫，不響應操作
        if self.is_reviving:
            if self.revive_frames:
                revive_anim_interval = 0.08
                self.revive_anim_timer += dt
                if self.revive_anim_timer >= revive_anim_interval:
                    self.revive_anim_frame += 1
                    self.revive_anim_timer = 0.0
                if self.revive_anim_frame >= len(self.revive_frames):
                    self.is_reviving = False
                    self.revive_anim_frame = 0
                    self.image = self.walk_frames[0]
                    self.current_frame = 0
                else:
                    frame = self.revive_frames[self.revive_anim_frame]
                    if self.facing_left:
                        frame = pygame.transform.flip(frame, True, False)
                    self.image = frame
            else:
                # 沒有復活動畫則直接結束
                self.is_reviving = False
            return

        if not self.is_alive:
            if self.is_shaking:
                self.shake_timer -= dt
                if self.shake_timer > 0 and self.original_death_pos_for_shake:
                    offset_x = random.uniform(-self.shake_magnitude, self.shake_magnitude)
                    offset_y = random.uniform(-self.shake_magnitude, self.shake_magnitude)
                    self.rect.centerx = self.original_death_pos_for_shake.x + offset_x
                    self.rect.centery = self.original_death_pos_for_shake.y + offset_y
                    # self.pos should remain self.original_death_pos_for_shake
                else:  # Shake ended
                    self.is_shaking = False
                    self.shake_timer = 0.0
                    if self.death_pos:  # Snap to final death position
                        self.pos = self.death_pos
                        self.rect.center = self.death_pos
                    # else: Error case, death_pos should be set
                self._update_dead_image()  # Update visual to dead sprite (especially after shake)
            else:  # Not shaking, just dead and static
                self._update_dead_image()
            return

        keys = pygame.key.get_pressed()
        movement_vector = pygame.math.Vector2(0, 0)

        mirror_active = effect_manager and effect_manager.is_mirror_active(self.player_id)

        up_key_actual = self.control_keys['down'] if mirror_active else self.control_keys['up']
        down_key_actual = self.control_keys['up'] if mirror_active else self.control_keys['down']
        left_key_actual = self.control_keys['right'] if mirror_active else self.control_keys['left']
        right_key_actual = self.control_keys['left'] if mirror_active else self.control_keys['right']

        if keys[up_key_actual]: movement_vector.y = -1
        if keys[down_key_actual]: movement_vector.y = 1
        if keys[left_key_actual]: movement_vector.x = -1
        if keys[right_key_actual]: movement_vector.x = 1

        # Determine facing direction based on NON-MIRRORED input for animation
        if keys[self.control_keys['left']]:
            self.facing_left = True
        elif keys[self.control_keys['right']]:
            self.facing_left = False

        is_moving = movement_vector.length_squared() > 0

        if is_moving:
            movement_vector.normalize_ip()
            movement_vector *= PLAYER_SPEED

        tentative_pos = self.pos + movement_vector

        # Store original rect for collision detection before moving
        original_rect = self.rect.copy()

        # Tentative rects for X and Y movement
        temp_rect_x = original_rect.copy()
        temp_rect_x.centerx = tentative_pos.x

        temp_rect_y = original_rect.copy()
        temp_rect_y.centery = tentative_pos.y

        # Laser Wall Collision
        # Walls are always collidable. Their visual appearance is handled by alpha.
        collided_with_laser = False
        for lw in laser_walls:  # laser_walls is the sprite group
            if temp_rect_x.colliderect(lw.rect):
                movement_vector.x = 0
                if not original_rect.colliderect(lw.rect):
                    collided_with_laser = True;
                    break
            if temp_rect_y.colliderect(lw.rect):  # Check Y collision separately
                movement_vector.y = 0
                if not original_rect.colliderect(lw.rect):
                    collided_with_laser = True;
                    break
        if collided_with_laser:
            self.die()
            return

        # Update tentative_pos based on adjusted movement_vector (if hit laser)
        tentative_pos = self.pos + movement_vector
        temp_rect_x.centerx = tentative_pos.x
        temp_rect_y.centery = tentative_pos.y

        # Coop Box Collision
        if coop_boxes:
            for box in coop_boxes:
                if temp_rect_x.colliderect(box.rect):
                    movement_vector.x = 0
                if temp_rect_y.colliderect(box.rect):  # Check against the original Y rect if X was blocked
                    movement_vector.y = 0

        # Update tentative_pos again
        tentative_pos = self.pos + movement_vector
        # Create a final tentative rect for spike and meteor collision
        final_tentative_rect = self.rect.copy()
        final_tentative_rect.center = tentative_pos

        # Spike Trap Collision
        if spike_trap_group:
            for spike in spike_trap_group:
                # Player attempts to move into the spike's area
                if spike.is_dangerous() and final_tentative_rect.colliderect(spike.rect):
                    # Death should occur at self.pos (position *before* moving into spike)
                    self.die()
                    return  # Exit update_movement

        # Meteor Collision
        if meteor_sprites:
            for meteor in meteor_sprites:
                # Player attempts to move into the meteor's area
                if final_tentative_rect.colliderect(meteor.rect):
                    # Death should occur at self.pos (position *before* moving into meteor)
                    self.die()
                    return  # Exit update_movement

        # Final position update
        self.pos += movement_vector
        self.pos.x = max(self.rect.width // 2, min(self.pos.x, SCREEN_WIDTH - self.rect.width // 2))
        self.pos.y = max(self.rect.height // 2, min(self.pos.y, SCREEN_HEIGHT - self.rect.height // 2))
        self.rect.center = self.pos

        self._update_alive_image(is_moving)

    def _update_alive_image(self, is_moving):
        """更新存活狀態的圖片"""
        # keys = pygame.key.get_pressed() # facing_left is now handled in update_movement
        # if keys[self.control_keys['left']]: self.facing_left = True
        # elif keys[self.control_keys['right']]: self.facing_left = False

        if is_moving:
            self.frame_timer += 1 / FPS
            if self.frame_timer >= self.frame_interval:
                self.current_frame = (self.current_frame + 1) % len(self.walk_frames)
                self.frame_timer = 0
            frame = self.walk_frames[self.current_frame]
        else:
            if not self.idle_frames:
                frame = self.walk_frames[0]
                self.current_frame = 0
            else:
                if self.current_frame >= len(self.idle_frames):  # Reset if switched from walk
                    self.current_frame = 0
                self.frame_timer += 1 / FPS
                # Ensure idle_frame_interval is defined, otherwise use frame_interval
                current_idle_interval = getattr(self, 'idle_frame_interval', self.frame_interval)
                if self.frame_timer >= current_idle_interval:
                    self.current_frame = (self.current_frame + 1) % len(self.idle_frames)
                    self.frame_timer = 0
                frame = self.idle_frames[self.current_frame]

        if self.facing_left:
            frame = pygame.transform.flip(frame, True, False)

        self.image = frame

    def _update_dead_image(self):
        """更新死亡状态的图片"""
        if self.death_frames:
            # 死亡动画逐帧播放
            self.frame_timer += 1 / FPS
            death_anim_interval = 0.08  # 每帧间隔
            if self.current_frame < len(self.death_frames) - 1:
                if self.frame_timer >= death_anim_interval:
                    self.current_frame += 1
                    self.frame_timer = 0
            frame = self.death_frames[self.current_frame]
            if self.facing_left:
                frame = pygame.transform.flip(frame, True, False)
            self.image = frame

    def draw(self, surface):
        surface.blit(self.image, self.rect)

    def _make_grayscale(self, surface):  # Keep this utility if needed elsewhere
        grayscale_surface = surface.copy()
        arr = pygame.surfarray.pixels3d(grayscale_surface)
        gray = (arr[:, :, 0] * 0.299 + arr[:, :, 1] * 0.587 + arr[:, :, 2] * 0.114).astype(arr.dtype)
        arr[:, :, 0] = gray
        arr[:, :, 1] = gray
        arr[:, :, 2] = gray
        del arr
        return grayscale_surface
