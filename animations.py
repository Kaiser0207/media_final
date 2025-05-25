import pygame
import os

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