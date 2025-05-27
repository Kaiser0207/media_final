import pygame
from animations import *
from boss_entities import ThrowableObject # <--- ADD THIS LINE
# 如有需要，导入 math、random 及 main.py 里用到的常量
import random

SCREEN_WIDTH = 1080
SCREEN_HEIGHT = 720
PLAYER_RADIUS = 15
PLAYER_SPEED = 3
FPS = 60

# Define new keys if they aren't defined in main.py and passed
# For P1 (Knight)
ACTION_KEY_P1 = pygame.K_g  # For pickup/throw by P1
# For P2 (Witch)
DRAW_ITEM_KEY_P2 = pygame.K_SEMICOLON  # For "drawing" an item by P2


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
        self.revive_frames = []
        self.is_invincible = False
        self.invincibility_duration = 2.0  # Seconds
        self.invincibility_timer = 0.0
        self.flash_timer = 0.0
        self.flash_interval = 0.1  # Seconds, for how quickly the player flashes
        self.is_currently_visible = True  # To toggle visibility for flashing effect

        if self.player_id == 0:  # Knight (P1)
            self.walk_frames = Knight_animation.load_knight_run_animation(target_width=PLAYER_RADIUS * 3,
                                                                          target_height=PLAYER_RADIUS * 3)
            self.idle_frames = Knight_animation.load_knight_idle_animation(target_width=PLAYER_RADIUS * 3,
                                                                           target_height=PLAYER_RADIUS * 3)
            self.death_frames = Knight_animation.load_knight_death_animation(target_width=PLAYER_RADIUS * 3,
                                                                             target_height=PLAYER_RADIUS * 3)
            self.revive_frames = Knight_animation.load_knight_revive_animation(target_width=PLAYER_RADIUS * 3,
                                                                               target_height=PLAYER_RADIUS * 3)
            self.is_witch = False
        elif self.player_id == 1:  # Witch (P2)
            self.is_witch = True
            self.walk_frames = Witch_animation.load_witch_run_animation(target_width=PLAYER_RADIUS * 3,
                                                                        target_height=PLAYER_RADIUS * 3)
            self.idle_frames = Witch_animation.load_witch_idle_animation(target_width=PLAYER_RADIUS * 3,
                                                                         target_height=PLAYER_RADIUS * 3)
            self.death_frames = Witch_animation.load_witch_death_animation(target_width=PLAYER_RADIUS * 3,
                                                                           target_height=PLAYER_RADIUS * 3)
            self.revive_frames = Witch_animation.load_witch_revive_animation(target_width=PLAYER_RADIUS * 3,
                                                                             target_height=PLAYER_RADIUS * 3)
            if self.player_id == 1:  # Witch
                print(
                    f"Witch revive_frames length: {len(self.revive_frames) if self.revive_frames else 'None or Empty'}")
                if self.revive_frames:
                    for i, f in enumerate(self.revive_frames):
                        if not isinstance(f, pygame.Surface):
                            print(f"Witch revive_frame {i} is not a Surface: {type(f)}")

        self.frame_interval = 0.2
        self.idle_frame_interval = 0.3

        # self.dead_frames = [] # This was overriding loaded death_frames with transparent walk_frames
        # for frame in self.walk_frames:
        #     dead_frame = frame.copy()
        #     dead_frame.set_alpha(100)
        #     self.dead_frames.append(dead_frame)

        self.current_frame = 0
        self.frame_timer = 0
        self.image = self.walk_frames[0] if self.walk_frames else pygame.Surface([PLAYER_RADIUS * 2, PLAYER_RADIUS * 2])
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

        # Boss level attributes
        self.held_object = None
        self.can_spawn_item_timer = 0  # Cooldown for P2 spawning items
        self.item_spawn_cooldown = 3.0  # Seconds

    def reset(self):
        self.pos = pygame.math.Vector2(self.start_pos.x, self.start_pos.y)
        self.is_alive = True
        self.death_pos = None
        self.image = self.walk_frames[0] if self.walk_frames else pygame.Surface([PLAYER_RADIUS * 2, PLAYER_RADIUS * 2])
        self.rect = self.image.get_rect(center=self.pos)
        self.current_frame = 0

        self.is_shaking = False
        self.shake_timer = 0.0
        self.original_death_pos_for_shake = None
        self.is_reviving = False
        self.revive_anim_timer = 0.0
        self.facing_left = False
        self.is_reviving = False
        self.revive_anim_frame = 0
        self.held_object = None
        self.can_spawn_item_timer = 0

        self.is_invincible = False
        self.invincibility_timer = 0.0
        self.flash_timer = 0.0
        self.is_currently_visible = True
        if hasattr(self, 'image') and self.image and self.walk_frames:
            self.image.set_alpha(255)
        elif self.walk_frames:
            pass

    def revive(self):
        print(f"Player {self.player_id} reviving. Revive frames available: {bool(self.revive_frames)}")
        self.is_alive = True
        if self.death_pos:
            self.pos = pygame.math.Vector2(self.death_pos.x, self.death_pos.y)
        else:
            self.pos = pygame.math.Vector2(self.start_pos.x, self.start_pos.y)

        self.rect.center = self.pos
        self.is_reviving = True
        self.revive_anim_timer = 0.0
        self.revive_anim_frame = 0
        self.current_frame = 0

        self.is_shaking = False
        self.shake_timer = 0.0
        self.original_death_pos_for_shake = None
        self.death_pos = None
        self.held_object = None  # Drop object on revive

        self.is_invincible = True
        self.invincibility_timer = self.invincibility_duration
        self.flash_timer = 0.0
        self.is_currently_visible = True
        if hasattr(self, 'image') and self.image:
            self.image.set_alpha(255)

    def update_invincibility_and_flash(self, dt):
        if self.is_invincible:
            self.invincibility_timer -= dt
            self.flash_timer -= dt

            if self.flash_timer <= 0:
                self.is_currently_visible = not self.is_currently_visible
                self.flash_timer = self.flash_interval

            if self.invincibility_timer <= 0:
                self.is_invincible = False
                self.is_currently_visible = True  # Ensure player is visible when invincibility ends

    def die(self, start_shake=True):  # Added optional shake parameter
        if self.is_invincible:  # Check for invincibility
            return

        if self.is_alive:
            self.is_alive = False
            if self.held_object:  # Drop object if holding one
                self.held_object.is_held = False
                self.held_object.held_by_player_id = None
                self.held_object = None

            # Store current position as death_pos if not already shaking from a previous death event
            if not self.is_shaking and self.death_pos is None:  # and not self.original_death_pos_for_shake
                self.death_pos = pygame.math.Vector2(self.pos.x, self.pos.y)
                self.original_death_pos_for_shake = pygame.math.Vector2(self.pos.x, self.pos.y)

            self.current_frame = 0  # Reset for death animation
            self.frame_timer = 0

            if start_shake:  # Start shake only if specified (e.g. hit by projectile)
                self.is_shaking = True
                self.shake_timer = self.shake_duration
                if not self.original_death_pos_for_shake:  # Ensure this is set if shaking starts
                    self.original_death_pos_for_shake = pygame.math.Vector2(self.pos.x, self.pos.y)
            else:  # If no shake, ensure static death pos
                self.is_shaking = False
                if not self.death_pos: self.death_pos = self.pos  # Fallback
                self.pos = self.death_pos
                self.rect.center = self.death_pos

    def update_boss_interactions(self, dt):
        if self.player_id == 1:  # P2 (Witch)
            if self.can_spawn_item_timer > 0:
                self.can_spawn_item_timer -= dt

    # Player.py
    def update_movement(self, laser_walls, coop_boxes=None, spike_trap_group=None, meteor_sprites=None,
                        effect_manager=None, dt=0.016,
                        # Boss level specific arguments
                        boss_entity=None, boss_projectiles=None, throwable_objects_group=None):
        self.update_invincibility_and_flash(dt)

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
                    self.image = self.walk_frames[0] if self.walk_frames else self.image  # Fallback
                    self.current_frame = 0
                else:
                    frame_surface = self.revive_frames[self.revive_anim_frame]
                    current_image = frame_surface.copy()

                    if self.facing_left:
                        frame = pygame.transform.flip(frame_surface, True, False) 
                    self.image = current_image
                    if self.is_invincible:
                        if not self.is_currently_visible:
                            self.image.set_alpha(100)
                        else:
                            self.image.set_alpha(255)
                    else:
                        self.image.set_alpha(255)
            else:
                self.is_reviving = False
                self.current_frame = 0
            if self.is_reviving:
                return

        if not self.is_alive:
            if self.is_shaking:
                self.shake_timer -= dt
                if self.shake_timer > 0 and self.original_death_pos_for_shake:
                    offset_x = random.uniform(-self.shake_magnitude, self.shake_magnitude)
                    offset_y = random.uniform(-self.shake_magnitude, self.shake_magnitude)
                    # Death animation should play based on self.current_frame updated in _update_dead_image
                    # The rect position is jittered, but self.pos remains the original death spot.
                    temp_shake_pos_x = self.original_death_pos_for_shake.x + offset_x
                    temp_shake_pos_y = self.original_death_pos_for_shake.y + offset_y
                    self.rect.center = (temp_shake_pos_x, temp_shake_pos_y)
                else:
                    self.is_shaking = False
                    self.shake_timer = 0.0
                    if self.death_pos:  # Snap visual rect to logical death position
                        self.rect.center = self.death_pos
                    # self.pos remains self.original_death_pos_for_shake or self.death_pos
                self._update_dead_image(dt)  # Pass dt for timed animation
            else:
                if self.death_pos: self.rect.center = self.death_pos  # Ensure rect is at final death pos
                self._update_dead_image(dt)  # Pass dt for timed animation
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

        if keys[self.control_keys['left']]:
            self.facing_left = True
        elif keys[self.control_keys['right']]:
            self.facing_left = False

        is_moving = movement_vector.length_squared() > 0
        if is_moving:
            movement_vector.normalize_ip()
            movement_vector *= PLAYER_SPEED

        tentative_pos = self.pos + movement_vector
        original_rect = self.rect.copy()
        temp_rect_x = original_rect.copy()
        temp_rect_x.centerx = tentative_pos.x
        temp_rect_y = original_rect.copy()
        temp_rect_y.centery = tentative_pos.y

        # --- Standard Obstacle Collisions ---
        # Laser Wall Collision
        if laser_walls:  # Check if laser_walls is not None (for boss level)
            collided_with_laser = False
            for lw in laser_walls:
                if temp_rect_x.colliderect(lw.rect) and (
                        not original_rect.colliderect(lw.rect) or movement_vector.x != 0):
                    movement_vector.x = 0;
                    collided_with_laser = True;
                    break
                if temp_rect_y.colliderect(lw.rect) and (
                        not original_rect.colliderect(lw.rect) or movement_vector.y != 0):
                    movement_vector.y = 0;
                    collided_with_laser = True;
                    break
            if collided_with_laser:
                self.die(start_shake=False);
                return  # No shake for wall collision

        tentative_pos = self.pos + movement_vector  # Re-evaluate tentative_pos
        temp_rect_x.centerx = tentative_pos.x
        temp_rect_y.centery = tentative_pos.y

        # Coop Box Collision
        if coop_boxes:
            for box in coop_boxes:
                if temp_rect_x.colliderect(box.rect): movement_vector.x = 0
                if temp_rect_y.colliderect(box.rect): movement_vector.y = 0

        tentative_pos = self.pos + movement_vector
        final_tentative_rect = self.rect.copy();
        final_tentative_rect.center = tentative_pos

        # Spike Trap Collision
        if spike_trap_group:
            for spike in spike_trap_group:
                if spike.is_dangerous() and final_tentative_rect.colliderect(spike.rect):
                    self.die(start_shake=False);
                    return

        # Meteor Collision
        if meteor_sprites:
            for meteor in meteor_sprites:
                if final_tentative_rect.colliderect(meteor.rect):
                    self.die(start_shake=True);
                    return  # Meteors cause shake

        # --- Boss Level Specific Collisions ---
        if boss_entity and boss_entity.current_health > 0:  # If boss is active
            # Player vs Boss direct collision (optional - make boss solid)
            if final_tentative_rect.colliderect(boss_entity.rect):
                # Simple bounce back
                if temp_rect_x.colliderect(boss_entity.rect): movement_vector.x = 0
                if temp_rect_y.colliderect(boss_entity.rect): movement_vector.y = 0
                # Or player takes damage/dies
                # self.die(start_shake=True); return

        if boss_projectiles:  # Collision with boss projectiles
            for proj in boss_projectiles:
                if final_tentative_rect.colliderect(proj.rect):
                    self.die(start_shake=True)  # Player dies if hit by boss projectile
                    proj.kill()  # Remove projectile
                    return  # Stop further updates this frame

        # Final position update
        self.pos += movement_vector
        self.pos.x = max(self.rect.width // 2, min(self.pos.x, SCREEN_WIDTH - self.rect.width // 2))
        self.pos.y = max(self.rect.height // 2, min(self.pos.y, SCREEN_HEIGHT - self.rect.height // 2))
        self.rect.center = self.pos

        # Update held object's position if any
        if self.held_object:
            self.held_object.update(dt, self.pos, self.facing_left)

        self._update_alive_image(is_moving, dt)  # Pass dt for timed animation

    def _update_alive_image(self, is_moving, dt):  # Added dt
        if is_moving:
            self.frame_timer += dt  # Use dt
            if self.frame_timer >= self.frame_interval:
                self.current_frame = (self.current_frame + 1) % (len(self.walk_frames) if self.walk_frames else 1)
                self.frame_timer = 0
            frame = self.walk_frames[self.current_frame] if self.walk_frames else self.image
        else:
            if not self.idle_frames:
                frame = self.walk_frames[0] if self.walk_frames else self.image
                self.current_frame = 0
            else:
                if self.current_frame >= len(self.idle_frames):
                    self.current_frame = 0
                self.frame_timer += dt  # Use dt
                current_idle_interval = getattr(self, 'idle_frame_interval', self.frame_interval)
                if self.frame_timer >= current_idle_interval:
                    self.current_frame = (self.current_frame + 1) % len(self.idle_frames)
                    self.frame_timer = 0
                frame = self.idle_frames[self.current_frame]

        if self.facing_left:
            frame = pygame.transform.flip(frame, True, False)
        self.image = frame

        if self.is_invincible:
            if not self.is_currently_visible:
                self.image.set_alpha(100)
            else:
                self.image.set_alpha(255)
        else:
            self.image.set_alpha(255)

    def _update_dead_image(self, dt):  # Added dt
        if self.death_frames:
            death_anim_interval = 0.08
            self.frame_timer += dt  # Use dt

            # Only advance frame if animation is not finished
            if self.current_frame < len(self.death_frames) - 1:
                if self.frame_timer >= death_anim_interval:
                    self.current_frame += 1
                    self.frame_timer = 0

            frame_to_draw = self.death_frames[self.current_frame]
            if self.facing_left:
                frame_to_draw = pygame.transform.flip(frame_to_draw, True, False)
            self.image = frame_to_draw
        # else: # Fallback if no death frames (e.g. use dead_color)
        # pass # Current implementation relies on death_frames

    def draw(self, surface):  # Mostly for debug, sprite groups handle drawing
        surface.blit(self.image, self.rect)
        # If holding an object, it's drawn by its own group or after players.

    # --- Boss Level Specific Actions ---
    def handle_action_key(self, throwable_objects_group):
        if self.player_id == 0 and self.is_alive:  # P1 (Knight) handles pickup/throw
            if self.held_object:
                # Throw object
                throw_dir = pygame.math.Vector2(1, -0.5) if not self.facing_left else pygame.math.Vector2(-1, -0.5)
                self.held_object.throw(throw_dir.normalize())
                # self.held_object.pos = self.pos + (throw_dir.normalize() * PLAYER_RADIUS * 2) # Move it out slightly
                self.held_object.rect.center = self.held_object.pos
                if self.held_object not in throwable_objects_group:  # Ensure it's in the group to be updated/drawn
                    throwable_objects_group.add(self.held_object)
                self.held_object = None
            else:
                # Try to pick up an object
                for obj in throwable_objects_group:
                    if not obj.is_held and self.rect.colliderect(obj.rect.inflate(20, 20)):  # Check wider radius
                        self.held_object = obj
                        obj.pickup(self.player_id)
                        # throwable_objects_group.remove(obj) # Remove from group while held, or just flag
                        break
        return None  # No object spawned here

    def handle_draw_item_key(self, throwable_objects_group, other_player_pos):  # P2 (Witch)
        if self.player_id == 1 and self.is_alive and self.can_spawn_item_timer <= 0:
            self.can_spawn_item_timer = self.item_spawn_cooldown  # Reset cooldown
            # Spawn item near P1 (other_player_pos) or a fixed spot
            spawn_x = other_player_pos.x + random.randint(-PLAYER_RADIUS * 2, PLAYER_RADIUS * 2)
            spawn_y = other_player_pos.y - PLAYER_RADIUS  # Slightly above P1

            spawn_x = max(PLAYER_RADIUS, min(spawn_x, SCREEN_WIDTH - PLAYER_RADIUS))
            spawn_y = max(PLAYER_RADIUS, min(spawn_y, SCREEN_HEIGHT - PLAYER_RADIUS))

            new_obj = ThrowableObject(spawn_x, spawn_y, self.player_id) #
            throwable_objects_group.add(new_obj)
            return new_obj  # Return the spawned object
        return None