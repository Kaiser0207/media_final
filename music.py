import pygame

# --- 音樂初始化 ---
pygame.mixer.init()

def play_music(file_path):
    pygame.mixer.music.stop()  # 停止當前音樂
    pygame.mixer.music.load(file_path)  # 加載新音樂
    pygame.mixer.music.play(-1)  # 循環播放

