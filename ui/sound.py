"""音效管理模块"""
import os
import pygame


class SoundManager:
    """管理游戏音效的加载和播放"""

    def __init__(self):
        self.enabled = True
        self.sounds = {}
        self._available = False
        self._init_mixer()

    def _init_mixer(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=1)
            self._available = True
        except Exception:
            self._available = False

    def load(self, name, filepath):
        """加载音效文件"""
        if not self._available:
            return
        if not os.path.exists(filepath):
            print(f"音效文件不存在: {filepath}")
            return
        try:
            self.sounds[name] = pygame.mixer.Sound(filepath)
        except Exception as e:
            print(f"加载音效失败 {filepath}: {e}")

    def play(self, name):
        """播放音效"""
        if not self.enabled or not self._available:
            return
        sound = self.sounds.get(name)
        if sound:
            try:
                sound.play()
            except Exception:
                pass

    def toggle(self):
        """切换音效开关"""
        self.enabled = not self.enabled
        return self.enabled
