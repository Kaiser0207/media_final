import pygame
import time
import threading

# --- 音樂初始化 ---
pygame.mixer.init()

def play_music(file_path):
    pygame.mixer.music.stop()  # 停止當前音樂
    pygame.mixer.music.load(file_path)  # 加載新音樂
    pygame.mixer.music.play(-1)  # 循環播放

def fade_out_and_switch_music(current_file, next_file, fade_duration=2):
    def fade_thread():
        pygame.mixer.music.load(current_file)  # 加載當前音樂
        pygame.mixer.music.play(-1)  # 循環播放當前音樂

        # 漸變音量到 0
        start_time = time.time()
        initial_volume = pygame.mixer.music.get_volume()
        while time.time() - start_time < fade_duration:
            elapsed = time.time() - start_time
            new_volume = max(0, initial_volume * (1 - elapsed / fade_duration))
            pygame.mixer.music.set_volume(new_volume)
            time.sleep(0.1)  # 減少 CPU 使用

        pygame.mixer.music.stop()  # 停止當前音樂

        # 切換到下一首音樂
        pygame.mixer.music.load(next_file)
        pygame.mixer.music.set_volume(initial_volume)  # 恢復音量
        pygame.mixer.music.play(-1)  # 循環播放新音樂

    threading.Thread(target=fade_thread, daemon=True).start()

