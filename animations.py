import pygame
import os

class Witch_animation:
    # 定义一个函数来加载并切割女巫的奔跑精灵图集
    def load_witch_run_animation(target_width, target_height):
        # 尝试从两个路径加载女巫奔跑动画的精灵图集
        witch_sprite_sheet_path = "./plays_animation_art/B_witch_run.png"
        if not os.path.exists(witch_sprite_sheet_path):
            witch_sprite_sheet_path = "B_witch_run.png"
            if not os.path.exists(witch_sprite_sheet_path):
                raise FileNotFoundError(f"女巫奔跑动画图片未找到: {witch_sprite_sheet_path} 或 ./plays_animation_art/B_witch_run.png")

        # 加载图片并保留透明通道
        witch_sprite_sheet = pygame.image.load(witch_sprite_sheet_path).convert_alpha()
        # 获取整张图的宽度和每帧的高度（8帧竖直排列）
        witch_frame_width = witch_sprite_sheet.get_width()
        witch_frame_height = witch_sprite_sheet.get_height() // 8

        frames = []
        for i in range(8):
            # 切割出每一帧
            frame = witch_sprite_sheet.subsurface((0, i * witch_frame_height, witch_frame_width, witch_frame_height))
            # 裁剪掉透明边界
            crop_rect = frame.get_bounding_rect()
            cropped = frame.subsurface(crop_rect)
            # 缩放到目标尺寸
            scaled_frame = pygame.transform.smoothscale(cropped, (target_width, target_height))
            frames.append(scaled_frame)
        return frames

    # 定义一个函数来加载并切割女巫的闲置精灵图集
    def load_witch_idle_animation(target_width, target_height):
        # 尝试从两个路径加载女巫闲置动画的精灵图集
        idle_sprite_sheet_path = "./plays_animation_art/B_witch_idle.png"
        if not os.path.exists(idle_sprite_sheet_path):
            idle_sprite_sheet_path = "B_witch_idle.png"
            if not os.path.exists(idle_sprite_sheet_path):
                raise FileNotFoundError(f"女巫闲置动画图片未找到: {idle_sprite_sheet_path} 或 ./plays_animation_art/B_witch_idle.png")

        # 加载图片并保留透明通道
        idle_sprite_sheet = pygame.image.load(idle_sprite_sheet_path).convert_alpha()
        num_idle_frames = 6
        # 获取整张图的宽度和每帧的高度（6帧竖直排列）
        idle_frame_width = idle_sprite_sheet.get_width()
        idle_frame_height = idle_sprite_sheet.get_height() // num_idle_frames

        frames = []
        for i in range(num_idle_frames):
            # 切割出每一帧
            frame = idle_sprite_sheet.subsurface((0, i * idle_frame_height, idle_frame_width, idle_frame_height))
            # 裁剪掉透明边界
            crop_rect = frame.get_bounding_rect()
            cropped = frame.subsurface(crop_rect)
            # 缩放到目标尺寸
            scaled_frame = pygame.transform.smoothscale(cropped, (target_width, target_height))
            frames.append(scaled_frame)
        return frames


    def load_witch_death_animation(target_width, target_height):
        """
        加载女巫死亡动画的精灵图集，并将其切割为单独的帧。
        Args:
            target_width (int): 最终缩放后的图片宽度。
            target_height (int): 最终缩放后的图片高度。
        Returns:
            list: 包含所有缩放后动画帧的列表。
        """
        death_sprite_sheet_path = "./plays_animation_art/B_witch_death.png"
        if not os.path.exists(death_sprite_sheet_path):
            death_sprite_sheet_path = "B_witch_death.png"
            if not os.path.exists(death_sprite_sheet_path):
                raise FileNotFoundError(f"女巫死亡动画图片未找到: {death_sprite_sheet_path} 或 ./plays_animation_art/B_witch_death.png")

        death_sprite_sheet = pygame.image.load(death_sprite_sheet_path).convert_alpha()
        num_death_frames = 10  # 死亡动画帧数
        death_frame_width = death_sprite_sheet.get_width()
        death_frame_height = death_sprite_sheet.get_height() // num_death_frames

        frames = []
        for i in range(6):
            # 切割出每一帧
            frame = death_sprite_sheet.subsurface((0, i * death_frame_height, death_frame_width, death_frame_height))
            # 裁剪掉透明边界
            crop_rect = frame.get_bounding_rect()
            cropped = frame.subsurface(crop_rect)
            # 缩放到目标尺寸
            scaled_frame = pygame.transform.smoothscale(cropped, (target_width, target_height))
            frames.append(scaled_frame)

        death_sprite_sheet_path = "./plays_animation_art/B_witch_death.png"
        if not os.path.exists(death_sprite_sheet_path):
            death_sprite_sheet_path = "B_witch_death.png"
            if not os.path.exists(death_sprite_sheet_path):
                raise FileNotFoundError(f"女巫死亡动画图片未找到: {death_sprite_sheet_path} 或 ./plays_animation_art/B_witch_death.png")

        death_sprite_sheet = pygame.image.load(death_sprite_sheet_path).convert_alpha()
        num_death_frames = 12  # 死亡动画帧数
        death_frame_width = death_sprite_sheet.get_width()
        death_frame_height = death_sprite_sheet.get_height() // num_death_frames


        for i in range(num_death_frames):
            if i > 8:
                # 切割出每一帧
                frame = death_sprite_sheet.subsurface((0, i * death_frame_height, death_frame_width, death_frame_height))
                # 裁剪掉透明边界
                crop_rect = frame.get_bounding_rect()
                cropped = frame.subsurface(crop_rect)
                # 缩放到目标尺寸
                scaled_frame = pygame.transform.smoothscale(cropped, (target_width, target_height))
                frames.append(scaled_frame)

        return frames

    def load_witch_revive_animation(target_width, target_height):
        """
        Load the witch's revive animation by reversing the death animation frames.
        """
        frames = Witch_animation.load_witch_death_animation(target_width, target_height)
        return frames[::-1]

class Knight_animation:
    # 加载骑士的奔跑动画 (保持不变)
    def load_knight_run_animation(target_width, target_height):
        """
        加载骑士奔跑动画的精灵图集，并将其切割为单独的帧。
        Args:
            target_width (int): 最终缩放后的图片宽度。
            target_height (int): 最终缩放后的图片高度。
        Returns:
            list: 包含所有缩放后动画帧的列表。
        """
        knight_sprite_sheet_path = "./plays_animation_art/Knight_WALK.png" # 假设您将图片保存为这个名字

        if not os.path.exists(knight_sprite_sheet_path):
            raise FileNotFoundError(f"骑士奔跑动画图片未找到: {knight_sprite_sheet_path}")

        knight_sprite_sheet = pygame.image.load(knight_sprite_sheet_path).convert_alpha()

        # 根据提供的 Knight_WALK.png 图片，它有 8 帧，水平排列。
        # 每帧的宽度是整个图片宽度除以帧数，高度是整个图片高度。
        num_knight_frames = 8
        knight_frame_width = knight_sprite_sheet.get_width() // num_knight_frames
        knight_frame_height = knight_sprite_sheet.get_height()

        if knight_sprite_sheet.get_width() % num_knight_frames != 0:
            print(f"警告：Knight_WALK.png 的宽度 {knight_sprite_sheet.get_width()} 不是帧数 {num_knight_frames} 的整数倍，可能导致切割不准确！")

        frames = []
        for i in range(num_knight_frames):
            frame = knight_sprite_sheet.subsurface((i * knight_frame_width, 0, knight_frame_width, knight_frame_height))
            # 裁剪透明边
            crop_rect = frame.get_bounding_rect()
            cropped = frame.subsurface(crop_rect)
            # 再缩放
            scaled_frame = pygame.transform.smoothscale(cropped, (target_width, target_height))
            frames.append(scaled_frame)
        return frames

    # 新增的函数：加载骑士的闲置动画
    def load_knight_idle_animation(target_width, target_height):
        """
        加载骑士闲置动画的精灵图集，并将其切割为单独的帧。
        Args:
            target_width (int): 最终缩放后的图片宽度。
            target_height (int): 最终缩放后的图片高度。
        Returns:
            list: 包含所有缩放后动画帧的列表。
        """
        knight_idle_sprite_sheet_path = "./plays_animation_art/Knight_IDLE.png" # 假设您将图片保存为这个名字

        if not os.path.exists(knight_idle_sprite_sheet_path):
            raise FileNotFoundError(f"骑士闲置动画图片未找到: {knight_idle_sprite_sheet_path}")

        knight_idle_sprite_sheet = pygame.image.load(knight_idle_sprite_sheet_path).convert_alpha()

        # 根据提供的 Knight_IDLE.png 图片，它有 8 帧，水平排列。
        # 每帧的宽度是整个图片宽度除以帧数，高度是整个图片高度。
        num_knight_idle_frames = 7
        knight_idle_frame_width = knight_idle_sprite_sheet.get_width() // num_knight_idle_frames
        knight_idle_frame_height = knight_idle_sprite_sheet.get_height()

        if knight_idle_sprite_sheet.get_width() % num_knight_idle_frames != 0:
            print(f"警告：Knight_IDLE.png 的宽度 {knight_idle_sprite_sheet.get_width()} 不是帧数 {num_knight_idle_frames} 的整数倍，可能导致切割不准确！")

        frames = []
        for i in range(num_knight_idle_frames):
            frame = knight_idle_sprite_sheet.subsurface((i * knight_idle_frame_width, 0, knight_idle_frame_width, knight_idle_frame_height))
            crop_rect = frame.get_bounding_rect()
            cropped = frame.subsurface(crop_rect)
            scaled_frame = pygame.transform.smoothscale(cropped, (target_width, target_height))
            frames.append(scaled_frame)
        return frames

    def load_knight_death_animation(target_width, target_height):
        """
        Load the knight's death animation from Knight_DEATH.png, slice into frames, crop, and scale
        while maintaining aspect ratio within the target_width and target_height constraints.
        """
        knight_death_sprite_sheet_path = "./plays_animation_art/Knight_DEATH.png"
        if not os.path.exists(knight_death_sprite_sheet_path):
            knight_death_sprite_sheet_path = "Knight_DEATH.png"
            if not os.path.exists(knight_death_sprite_sheet_path):
                raise FileNotFoundError(f"骑士死亡动画图片未找到: {knight_death_sprite_sheet_path} 或 ./plays_animation_art/Knight_DEATH.png")

        knight_death_sprite_sheet = pygame.image.load(knight_death_sprite_sheet_path).convert_alpha()
        num_death_frames = 12
        frame_width = knight_death_sprite_sheet.get_width() // num_death_frames
        frame_height = knight_death_sprite_sheet.get_height()

        if knight_death_sprite_sheet.get_width() % num_death_frames != 0:
            print(f"警告：Knight_DEATH.png 的宽度 {knight_death_sprite_sheet.get_width()} 不是帧数 {num_death_frames} 的整数倍，可能导致切割不准确！")

        frames = []
        for i in range(num_death_frames):
            frame = knight_death_sprite_sheet.subsurface((i * frame_width, 0, frame_width, frame_height))
            crop_rect = frame.get_bounding_rect()
            cropped = frame.subsurface(crop_rect)

            original_cropped_width = cropped.get_width()
            original_cropped_height = cropped.get_height()

            if original_cropped_width == 0 or original_cropped_height == 0:
                frames.append(pygame.Surface((target_width, target_height), pygame.SRCALPHA))
                continue

            width_ratio = target_width / original_cropped_width
            height_ratio = target_height / original_cropped_height

            scale_ratio = min(width_ratio, height_ratio)

            new_width = int(original_cropped_width * scale_ratio)
            new_height = int(original_cropped_height * scale_ratio)

            if new_width == 0: new_width = 1
            if new_height == 0: new_height = 1

            scaled_frame = pygame.transform.smoothscale(cropped, (new_width, new_height))

            final_frame_surface = pygame.Surface((target_width, target_height), pygame.SRCALPHA)
            blit_x = (target_width - new_width) // 2
            blit_y = (target_height - new_height) // 2
            final_frame_surface.blit(scaled_frame, (blit_x, blit_y))

            frames.append(final_frame_surface)
        return frames

    def load_knight_revive_animation(target_width, target_height):
        """
        Load the knight's revive animation by reversing the death animation frames.
        """
        frames = Knight_animation.load_knight_death_animation(target_width, target_height)
        return frames[::-1]

class boss_animation:
    def split_boss_image_vertically(image_path):
        """
        Split the boss.png image vertically into 7 equal parts without scaling.

        Args:
            image_path (str): Path to the boss.png image.

        Returns:
            list: A list of pygame.Surface objects representing the split images.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Load the image
        boss_image = pygame.image.load(image_path).convert_alpha()
        frame_width = boss_image.get_width()
        frame_height = boss_image.get_height() // 7

        frames = []
        for i in range(7):
            # Slice each vertical segment
            frame = boss_image.subsurface((0, i * frame_height, frame_width, frame_height))
            frames.append(frame)

        return frames


    def load_boos_run_animation(target_width, target_height):
        """
        Load the boss run animation from the second vertical segment of the boss.png image.
        Args:
            target_width (int): Final scaled width of each frame.
            target_height (int): Final scaled height of each frame.
        Returns:
            list: A list of scaled pygame.Surface objects representing the animation frames.
        """
        # Get the second vertical segment
        boss_frames = boss_animation.split_boss_image_vertically("./plays_animation_art/boss.png")
        if len(boss_frames) < 2:
            raise ValueError("The boss.png image does not have enough vertical segments to extract the second part.")

        boss_sprite_sheet = boss_frames[1]  # Use the second vertical segment
        frame_width = boss_sprite_sheet.get_width() // 17  # Assuming 8 frames horizontally
        frame_height = boss_sprite_sheet.get_height()

        frames = []
        for i in range(8):
            # Slice each frame
            frame = boss_sprite_sheet.subsurface((i * frame_width, 0, frame_width, frame_height))
            # Scale the frame to the target dimensions
            scaled_frame = pygame.transform.smoothscale(frame, (target_width, target_height))
            frames.append(scaled_frame)

        return frames

    def load_boos_run2_animation(target_width, target_height):
        """
        Load the boss run animation from the second vertical segment of the boss.png image.
        Args:
            target_width (int): Final scaled width of each frame.
            target_height (int): Final scaled height of each frame.
        Returns:
            list: A list of scaled pygame.Surface objects representing the animation frames.
        """
        # Get the second vertical segment
        boss_frames = boss_animation.split_boss_image_vertically("./plays_animation_art/boss.png")
        if len(boss_frames) < 2:
            raise ValueError("The boss.png image does not have enough vertical segments to extract the second part.")

        boss_sprite_sheet = boss_frames[2]  # Use the second vertical segment
        frame_width = boss_sprite_sheet.get_width() // 17  # Assuming 8 frames horizontally
        frame_height = boss_sprite_sheet.get_height()

        frames = []
        for i in range(8):
            # Slice each frame
            frame = boss_sprite_sheet.subsurface((i * frame_width, 0, frame_width, frame_height))
            # Scale the frame to the target dimensions
            scaled_frame = pygame.transform.smoothscale(frame, (target_width, target_height))
            frames.append(scaled_frame)

        return frames

if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Boss Run Animation Test")
    clock = pygame.time.Clock()

    # Load boss run animation frames
    boss_run_frames = boss_animation.load_boos_run_animation(200,200)
    frame_index = 0

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill((0, 0, 0))  # Clear screen with black

        # Display the current frame
        screen.blit(boss_run_frames[frame_index], (300, 200))

        # Update frame index
        frame_index = (frame_index + 1) % len(boss_run_frames)

        pygame.display.flip()
        clock.tick(10)  # Limit to 10 frames per second

    pygame.quit()