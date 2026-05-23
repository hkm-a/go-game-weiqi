import pygame
import math
import os

class Colors:
    DARK_BG = (18, 18, 24)
    GOLD = (212, 175, 55)
    GOLD_LIGHT = (255, 223, 128)
    GOLD_DARK = (160, 130, 40)
    DARK_PANEL = (30, 30, 40)
    DARK_PANEL_HOVER = (45, 45, 55)
    TEXT_LIGHT = (230, 220, 200)
    TEXT_DARK = (30, 25, 20)
    RED = (200, 60, 60)
    GREEN = (60, 180, 100)
    BLUE = (80, 140, 220)

def get_chinese_font(size):
    """加载支持中文的字体"""
    font_paths = [
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/arial.ttf",
        None
    ]
    
    for font_path in font_paths:
        if font_path and os.path.exists(font_path):
            try:
                return pygame.font.Font(font_path, size)
            except:
                continue
    
    return pygame.font.Font(None, size)

class Button:
    def __init__(self, x, y, width, height, text, callback, 
                 color=Colors.DARK_PANEL, 
                 hover_color=Colors.DARK_PANEL_HOVER, 
                 text_color=Colors.TEXT_LIGHT, 
                 border_color=Colors.GOLD,
                 font_size=22,
                 style="default"):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.border_color = border_color
        self.font_size = font_size
        self.style = style
        self.is_hovered = False
        self.is_pressed = False
        self.font = get_chinese_font(font_size)
        self.click_animation = 0.0
        self.hover_animation = 0.0
        self.active = True
        self.visible = True  # False 时完全不绘制

    def update(self, dt):
        target_hover = 1.0 if self.is_hovered else 0.0
        self.hover_animation += (target_hover - self.hover_animation) * dt * 8
        
        if self.is_pressed:
            self.click_animation = 1.0
        else:
            self.click_animation *= (1.0 - dt * 8)
    
    def draw(self, surface):
        if not self.visible:
            return
        # 非活跃状态显示灰色
        if not self.active:
            inactive_color = (35, 35, 45)
            pygame.draw.rect(surface, inactive_color, self.rect, border_radius=12)
            pygame.draw.rect(surface, (50, 50, 60), self.rect, 2, border_radius=12)
            text_surface = self.font.render(self.text, True, (100, 100, 110))
            text_rect = text_surface.get_rect(center=self.rect.center)
            surface.blit(text_surface, text_rect)
            return
        
        current_color = (
            int(self.color[0] + (self.hover_color[0] - self.color[0]) * self.hover_animation),
            int(self.color[1] + (self.hover_color[1] - self.color[1]) * self.hover_animation),
            int(self.color[2] + (self.hover_color[2] - self.color[2]) * self.hover_animation)
        )
        
        press_offset = int(self.click_animation * 2)
        
        draw_rect = pygame.Rect(
            self.rect.x + press_offset,
            self.rect.y + press_offset,
            self.rect.width - press_offset * 2,
            self.rect.height - press_offset * 2
        )
        
        border_thickness = 2 + int(self.hover_animation * 2)
        
        glow_size = 8 + int(self.hover_animation * 4)
        if self.is_hovered:
            glow_surface = pygame.Surface((draw_rect.width + glow_size * 2, draw_rect.height + glow_size * 2), pygame.SRCALPHA)
            glow_alpha = int(80 * self.hover_animation)
            pygame.draw.rect(glow_surface, (*self.border_color, glow_alpha), 
                           (0, 0, draw_rect.width + glow_size * 2, draw_rect.height + glow_size * 2), 
                           border_radius=14)
            surface.blit(glow_surface, (draw_rect.x - glow_size, draw_rect.y - glow_size))
        
        pygame.draw.rect(surface, current_color, draw_rect, border_radius=12)
        pygame.draw.rect(surface, self.border_color, draw_rect, border_thickness, border_radius=12)
        
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=draw_rect.center)
        surface.blit(text_surface, text_rect)
    
    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)
    
    def handle_event(self, event):
        if not self.active:
            return False
        
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.is_hovered:
                self.is_pressed = True
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.is_pressed and self.is_hovered:
                self.is_pressed = False
                if self.callback:
                    self.callback()
            else:
                self.is_pressed = False

class DifficultyButton(Button):
    def __init__(self, x, y, width, height, text, callback, difficulty, is_selected=False):
        super().__init__(x, y, width, height, text, callback)
        self.difficulty = difficulty
        self.is_selected = is_selected
    
    def draw(self, surface):
        if not self.visible:
            return
        if self.is_selected:
            current_color = Colors.GOLD_DARK
            current_border = Colors.GOLD_LIGHT
            text_color = Colors.TEXT_DARK
        else:
            current_color = (
                int(self.color[0] + (self.hover_color[0] - self.color[0]) * self.hover_animation),
                int(self.color[1] + (self.hover_color[1] - self.color[1]) * self.hover_animation),
                int(self.color[2] + (self.hover_color[2] - self.color[2]) * self.hover_animation)
            )
            current_border = Colors.GOLD
            text_color = self.text_color
        
        press_offset = int(self.click_animation * 2)
        
        draw_rect = pygame.Rect(
            self.rect.x + press_offset,
            self.rect.y + press_offset,
            self.rect.width - press_offset * 2,
            self.rect.height - press_offset * 2
        )
        
        if self.is_selected or self.is_hovered:
            glow_size = 10
            glow_alpha = 120 if self.is_selected else int(60 * self.hover_animation)
            glow_surface = pygame.Surface((draw_rect.width + glow_size * 2, draw_rect.height + glow_size * 2), pygame.SRCALPHA)
            pygame.draw.rect(glow_surface, (*current_border, glow_alpha), 
                           (0, 0, draw_rect.width + glow_size * 2, draw_rect.height + glow_size * 2), 
                           border_radius=12)
            surface.blit(glow_surface, (draw_rect.x - glow_size, draw_rect.y - glow_size))
        
        pygame.draw.rect(surface, current_color, draw_rect, border_radius=10)
        border_thickness = 3 if self.is_selected else 2
        pygame.draw.rect(surface, current_border, draw_rect, border_thickness, border_radius=10)
        
        text_surface = self.font.render(self.text, True, text_color)
        text_rect = text_surface.get_rect(center=draw_rect.center)
        surface.blit(text_surface, text_rect)

class ToggleButton(Button):
    def __init__(self, x, y, width, height, text_on, text_off, callback, is_on=True):
        super().__init__(x, y, width, height, text_on, callback)
        self.text_on = text_on
        self.text_off = text_off
        self.is_on = is_on
        self.text = self.text_on if self.is_on else self.text_off
    
    def toggle(self):
        self.is_on = not self.is_on
        self.text = self.text_on if self.is_on else self.text_off
    
    def draw(self, surface):
        if not self.visible:
            return
        if self.is_on:
            current_color = Colors.GREEN
            current_border = (100, 220, 140)
        else:
            current_color = (50, 50, 60)
            current_border = Colors.GOLD
        
        current_color = (
            int(current_color[0] + 15 * self.hover_animation),
            int(current_color[1] + 15 * self.hover_animation),
            int(current_color[2] + 15 * self.hover_animation)
        )
        
        press_offset = int(self.click_animation * 2)
        
        draw_rect = pygame.Rect(
            self.rect.x + press_offset,
            self.rect.y + press_offset,
            self.rect.width - press_offset * 2,
            self.rect.height - press_offset * 2
        )
        
        pygame.draw.rect(surface, current_color, draw_rect, border_radius=10)
        pygame.draw.rect(surface, current_border, draw_rect, 2, border_radius=10)
        
        text_surface = self.font.render(self.text, True, Colors.TEXT_LIGHT)
        text_rect = text_surface.get_rect(center=draw_rect.center)
        surface.blit(text_surface, text_rect)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.is_hovered:
                self.is_pressed = True
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.is_pressed and self.is_hovered:
                self.is_pressed = False
                self.toggle()
                if self.callback:
                    self.callback()
            else:
                self.is_pressed = False

class UIManager:
    def __init__(self):
        self.components = []
    
    def add_component(self, component):
        self.components.append(component)
    
    def update(self, dt):
        for component in self.components:
            if hasattr(component, 'update'):
                component.update(dt)
    
    def handle_events(self, events):
        for event in events:
            for component in self.components:
                if hasattr(component, 'handle_event'):
                    component.handle_event(event)
    
    def draw(self, surface):
        for component in self.components:
            if hasattr(component, 'draw'):
                component.draw(surface)
