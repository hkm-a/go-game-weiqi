import pygame
import math
import random
import os

class Colors:
    DARK_BG = (18, 18, 24)
    GOLD = (212, 175, 55)
    GOLD_LIGHT = (255, 223, 128)
    WOOD_DARK = (98, 72, 32)
    WOOD_LIGHT = (205, 155, 85)
    WOOD_MID = (165, 120, 60)
    BLACK_STONE = (25, 25, 30)
    BLACK_STONE_HIGHLIGHT = (60, 60, 70)
    WHITE_STONE = (240, 240, 245)
    WHITE_STONE_SHADOW = (180, 180, 190)
    LINE_COLOR = (20, 15, 10)
    RED = (200, 60, 60)
    GREEN = (60, 180, 100)
    BLUE = (80, 140, 220)
    TEXT_LIGHT = (230, 220, 200)
    TEXT_DARK = (30, 25, 20)
    KO_THREAT_HIGH = (220, 80, 80)
    KO_THREAT_MEDIUM = (255, 150, 80)
    KO_THREAT_LOW = (255, 200, 150)

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

class Renderer:
    def __init__(self, screen, board_x, board_y, board_size):
        self.screen = screen
        self.board_x = board_x
        self.board_y = board_y
        self.board_size = board_size
        self.board_width = board_size
        self.board_height = board_size
        self.grid_size = 19
        self.cell_size = (self.board_width - 100) // (self.grid_size - 1)
        self.stone_radius = self.cell_size // 2 - 4
        self.star_point_radius = 5
        
        self.animation_time = 0
        self.particles = []
        
        self.star_points = [
            (3, 3), (3, 9), (3, 15),
            (9, 3), (9, 9), (9, 15),
            (15, 3), (15, 9), (15, 15)
        ]
        
        self.board_texture = self._generate_board_texture()
    
    def _generate_board_texture(self):
        texture = pygame.Surface((self.board_width, self.board_height))
        
        for y in range(self.board_height):
            for x in range(self.board_width):
                noise = random.randint(-15, 15)
                wood_ratio = (y / self.board_height) * 0.4 + 0.6
                r = int(Colors.WOOD_MID[0] * wood_ratio + Colors.WOOD_LIGHT[0] * (1 - wood_ratio)) + noise
                g = int(Colors.WOOD_MID[1] * wood_ratio + Colors.WOOD_LIGHT[1] * (1 - wood_ratio)) + noise
                b = int(Colors.WOOD_MID[2] * wood_ratio + Colors.WOOD_LIGHT[2] * (1 - wood_ratio)) + noise
                r = max(0, min(255, r))
                g = max(0, min(255, g))
                b = max(0, min(255, b))
                texture.set_at((x, y), (r, g, b))
        
        return texture
    
    def update(self, dt):
        self.animation_time += dt
        
        new_particles = []
        for p in self.particles:
            p['life'] -= dt
            p['y'] += p['vy'] * dt
            p['x'] += p['vx'] * dt
            p['alpha'] = int(p['life'] / p['max_life'] * 255)
            if p['life'] > 0:
                new_particles.append(p)
        self.particles = new_particles
    
    def add_place_particle(self, x, y, color):
        for _ in range(12):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(30, 80)
            self.particles.append({
                'x': x, 'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': 0.6, 'max_life': 0.6,
                'color': color, 'size': random.randint(2, 5),
                'alpha': 255
            })
    
    def draw_board(self, surface):
        bg_rect = pygame.Rect(0, 0, surface.get_width(), surface.get_height())
        pygame.draw.rect(surface, Colors.DARK_BG, bg_rect)
        
        board_rect = pygame.Rect(self.board_x, self.board_y, self.board_width, self.board_height)
        surface.blit(self.board_texture, board_rect.topleft)
        
        border_rect = pygame.Rect(self.board_x - 8, self.board_y - 8, self.board_width + 16, self.board_height + 16)
        pygame.draw.rect(surface, Colors.GOLD, border_rect, 4, border_radius=4)
        
        pygame.draw.rect(surface, Colors.WOOD_DARK, board_rect, 2, border_radius=2)
        
        start_x = self.board_x + 50
        start_y = self.board_y + 50
        
        for i in range(self.grid_size):
            x = start_x + i * self.cell_size
            pygame.draw.line(surface, Colors.LINE_COLOR, 
                           (x, start_y), 
                           (x, start_y + (self.grid_size - 1) * self.cell_size), 2)
            
            y = start_y + i * self.cell_size
            pygame.draw.line(surface, Colors.LINE_COLOR, 
                           (start_x, y), 
                           (start_x + (self.grid_size - 1) * self.cell_size, y), 2)
    
    def draw_star_points(self, surface):
        start_x = self.board_x + 50
        start_y = self.board_y + 50
        
        for (x, y) in self.star_points:
            px = start_x + x * self.cell_size
            py = start_y + y * self.cell_size
            
            pygame.draw.circle(surface, (0, 0, 0, 100), (int(px), int(py)), self.star_point_radius + 3)
            pygame.draw.circle(surface, Colors.LINE_COLOR, (int(px), int(py)), self.star_point_radius)
    
    def draw_stone(self, surface, x, y, color, alpha=255, placed_time=None):
        screen_pos = self.board_to_screen(x, y)
        if screen_pos is None:
            return
        
        cx, cy = screen_pos
        
        scale = 1.0
        if placed_time is not None:
            age = self.animation_time - placed_time
            if age < 0.2:
                scale = 0.8 + 0.2 * (age / 0.2)
        
        if color == 'B':
            self._draw_black_stone(surface, cx, cy, alpha, scale)
        elif color == 'W':
            self._draw_white_stone(surface, cx, cy, alpha, scale)
    
    def _draw_black_stone(self, surface, cx, cy, alpha=255, scale=1.0):
        radius = int(self.stone_radius * scale)
        
        shadow_radius = radius + 2
        shadow_x = cx + 3
        shadow_y = cy + 3
        
        if alpha == 255:
            pygame.draw.circle(surface, (0, 0, 0, 60), (shadow_x, shadow_y), shadow_radius)
        
        for r in range(radius, 0, -1):
            ratio = r / radius
            red = int(15 + 45 * ratio)
            green = int(15 + 45 * ratio)
            blue = int(20 + 40 * ratio)
            
            if alpha < 255:
                s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                pygame.draw.circle(s, (red, green, blue, alpha), (r, r), r)
                surface.blit(s, (cx - r, cy - r))
            else:
                pygame.draw.circle(surface, (red, green, blue), (cx, cy), r)
        
        highlight_radius = radius // 3
        highlight_x = cx - radius // 4
        highlight_y = cy - radius // 4
        
        for r in range(highlight_radius, 0, -1):
            ratio = r / highlight_radius
            gray = int(40 + 50 * ratio)
            if alpha == 255:
                pygame.draw.circle(surface, (gray, gray, min(255, gray + 15)), (highlight_x, highlight_y), r)
    
    def _draw_white_stone(self, surface, cx, cy, alpha=255, scale=1.0):
        radius = int(self.stone_radius * scale)
        
        shadow_radius = radius + 2
        shadow_x = cx + 3
        shadow_y = cy + 3
        
        if alpha == 255:
            pygame.draw.circle(surface, (0, 0, 0, 40), (shadow_x, shadow_y), shadow_radius)
        
        for r in range(radius, 0, -1):
            ratio = r / radius
            red = int(200 + 55 * ratio)
            green = int(200 + 55 * ratio)
            blue = int(205 + 50 * ratio)
            
            if alpha < 255:
                s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                pygame.draw.circle(s, (red, green, blue, alpha), (r, r), r)
                surface.blit(s, (cx - r, cy - r))
            else:
                pygame.draw.circle(surface, (red, green, blue), (cx, cy), r)
        
        if alpha == 255:
            pygame.draw.circle(surface, (150, 150, 160), (cx, cy), radius, 1)
        
        highlight_radius = radius // 3
        highlight_x = cx - radius // 5
        highlight_y = cy - radius // 4
        
        for r in range(highlight_radius, 0, -1):
            ratio = r / highlight_radius
            gray = min(255, int(235 + 20 * ratio))
            if alpha == 255:
                pygame.draw.circle(surface, (gray, gray, min(255, gray + 8)), (highlight_x, highlight_y), r)
    
    def draw_pieces(self, surface, board, placed_times=None):
        if placed_times is None:
            placed_times = {}
        
        for y in range(board.size):
            for x in range(board.size):
                stone = board.get_stone(x, y)
                if stone is not None:
                    placed_time = placed_times.get((x, y))
                    self.draw_stone(surface, x, y, stone, placed_time=placed_time)
        
        for p in self.particles:
            s = pygame.Surface((p['size']*2, p['size']*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*p['color'], p['alpha']), (p['size'], p['size']), p['size'])
            surface.blit(s, (p['x'] - p['size'], p['y'] - p['size']))
    
    def draw_ko_threats(self, surface, ko_threats, threat_scores):
        """绘制劫材提示位置"""
        start_x = self.board_x + 50
        start_y = self.board_y + 50
        
        for pos in ko_threats:
            grid_x, grid_y = pos
            screen_x = start_x + grid_x * self.cell_size
            screen_y = start_y + grid_y * self.cell_size
            
            score = threat_scores.get(pos, 0)
            
            if score >= 70:
                color = Colors.KO_THREAT_HIGH
                radius = self.stone_radius // 2
                alpha = 200
            elif score >= 40:
                color = Colors.KO_THREAT_MEDIUM
                radius = self.stone_radius // 3
                alpha = 180
            else:
                color = Colors.KO_THREAT_LOW
                radius = self.stone_radius // 4
                alpha = 160
            
            ko_surface = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(ko_surface, (*color, alpha), (radius + 2, radius + 2), radius)
            pygame.draw.circle(ko_surface, (*color, 255), (radius + 2, radius + 2), radius, 2)
            
            surface.blit(ko_surface, (screen_x - radius - 2, screen_y - radius - 2))
    
    def draw_influence_map(self, surface, influence_map):
        start_x = self.board_x + 50
        start_y = self.board_y + 50
        
        try:
            for y in range(self.grid_size):
                for x in range(self.grid_size):
                    if y >= len(influence_map) or x >= len(influence_map[y]):
                        continue
                    influence = influence_map[y][x]
                    cx = start_x + x * self.cell_size
                    cy = start_y + y * self.cell_size
                    
                    if influence > 0.1:
                        alpha = min(int(abs(influence) * 60), 90)
                        s = pygame.Surface((self.cell_size + 4, self.cell_size + 4), pygame.SRCALPHA)
                        pygame.draw.circle(s, (80, 120, 255, alpha), (self.cell_size//2 + 2, self.cell_size//2 + 2), self.cell_size//2 - 4)
                        surface.blit(s, (cx - self.cell_size//2 - 2, cy - self.cell_size//2 - 2))
                    elif influence < -0.1:
                        alpha = min(int(abs(influence) * 60), 90)
                        s = pygame.Surface((self.cell_size + 4, self.cell_size + 4), pygame.SRCALPHA)
                        pygame.draw.circle(s, (255, 100, 100, alpha), (self.cell_size//2 + 2, self.cell_size//2 + 2), self.cell_size//2 - 4)
                        surface.blit(s, (cx - self.cell_size//2 - 2, cy - self.cell_size//2 - 2))
        except Exception as e:
            print(f"draw_influence_map error: {e}")
            pass
    
    def draw_hints(self, surface, best_moves, max_hints=3):
        start_x = self.board_x + 50
        start_y = self.board_y + 50
        
        colors = [(0, 230, 120, 200), (80, 200, 255, 170), (255, 180, 50, 140)]
        
        for i, (move, score) in enumerate(best_moves[:max_hints]):
            x, y = move
            cx = start_x + x * self.cell_size
            cy = start_y + y * self.cell_size
            color = colors[i] if i < len(colors) else colors[-1]
            
            pulse = (math.sin(self.animation_time * 3 + i) + 1) * 0.5
            pulse_radius = int(self.stone_radius * (0.8 + pulse * 0.3))
            
            s = pygame.Surface((pulse_radius * 4, pulse_radius * 4), pygame.SRCALPHA)
            
            pygame.draw.circle(s, color, (pulse_radius * 2, pulse_radius * 2), pulse_radius)
            pygame.draw.circle(s, (255, 255, 255, color[3] // 2), (pulse_radius * 2, pulse_radius * 2), pulse_radius - 6)
            
            rank_surface = get_chinese_font(28).render(str(i + 1), True, (30, 30, 40))
            rank_rect = rank_surface.get_rect(center=(pulse_radius * 2, pulse_radius * 2))
            s.blit(rank_surface, rank_rect)
            
            surface.blit(s, (cx - pulse_radius * 2, cy - pulse_radius * 2))
    
    def screen_to_board(self, pos):
        sx, sy = pos
        start_x = self.board_x + 50
        start_y = self.board_y + 50
        
        bx = round((sx - start_x) / self.cell_size)
        by = round((sy - start_y) / self.cell_size)
        
        if 0 <= bx < self.grid_size and 0 <= by < self.grid_size:
            return (bx, by)
        return None
    
    def board_to_screen(self, x, y):
        if not (0 <= x < self.grid_size and 0 <= y < self.grid_size):
            return None
        
        start_x = self.board_x + 50
        start_y = self.board_y + 50
        
        sx = start_x + x * self.cell_size
        sy = start_y + y * self.cell_size
        
        return (int(sx), int(sy))
    
    def draw_sidebar_panel(self, surface, x, y, width, height, title=""):
        panel_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, (30, 30, 40), panel_rect, border_radius=12)
        pygame.draw.rect(surface, Colors.GOLD, panel_rect, 2, border_radius=12)
        
        if title:
            title_font = get_chinese_font(24)
            title_surface = title_font.render(title, True, Colors.GOLD_LIGHT)
            surface.blit(title_surface, (x + 15, y + 12))
            
            pygame.draw.line(surface, Colors.GOLD, (x + 15, y + 38), (x + width - 15, y + 38), 1)
        
        return panel_rect
    
    def draw_current_player(self, surface, current_player, move_count, captures, game_status=None, winner=None, final_score=None, info_y=None):
        font = get_chinese_font(28)
        small_font = get_chinese_font(24)
        
        info_x = self.board_x + self.board_width + 50
        if info_y is None:
            info_y = self.board_y + 30
        
        panel_width = 260
        panel_height = 300 if game_status == 'ended' else 200
        
        self.draw_sidebar_panel(surface, info_x - 15, info_y - 15, panel_width, panel_height, "游戏状态")
        
        info_x += 5
        info_y += 35
        
        if game_status == 'ended':
            player_text = "游戏结束!"
            text_color = Colors.GOLD_LIGHT
        else:
            player_text = "轮到: 黑方" if current_player == 'B' else "轮到: 白方"
            text_color = (220, 220, 230) if current_player == 'W' else Colors.GOLD_LIGHT
        
        player_surface = font.render(player_text, True, text_color)
        surface.blit(player_surface, (info_x, info_y))
        
        if game_status == 'ended':
            winner_text = "黑方获胜!" if winner == 'B' else "白方获胜!"
            winner_color = Colors.GOLD_LIGHT
            winner_surface = font.render(winner_text, True, winner_color)
            surface.blit(winner_surface, (info_x, info_y + 35))
            
            if final_score:
                score_text1 = f"黑方: {final_score['black']:.1f}子"
                score_text2 = f"白方: {final_score['white']:.1f}子"
                score1_surface = small_font.render(score_text1, True, Colors.TEXT_LIGHT)
                score2_surface = small_font.render(score_text2, True, Colors.TEXT_LIGHT)
                surface.blit(score1_surface, (info_x, info_y + 70))
                surface.blit(score2_surface, (info_x, info_y + 95))
                
                stones_text1 = f"棋子: {final_score.get('black_stones', 0)}"
                stones_text2 = f"棋子: {final_score.get('white_stones', 0)}"
                stones1_surface = small_font.render(stones_text1, True, (150, 150, 170))
                stones2_surface = small_font.render(stones_text2, True, (150, 150, 170))
                surface.blit(stones1_surface, (info_x, info_y + 120))
                surface.blit(stones2_surface, (info_x, info_y + 145))
                
                terr_text1 = f"领地: {final_score.get('black_territory', 0)}"
                terr_text2 = f"领地: {final_score.get('white_territory', 0)}"
                terr1_surface = small_font.render(terr_text1, True, (150, 150, 170))
                terr2_surface = small_font.render(terr_text2, True, (150, 150, 170))
                surface.blit(terr1_surface, (info_x, info_y + 170))
                surface.blit(terr2_surface, (info_x, info_y + 195))
            
            move_text = f"总手数: {move_count}"
            move_surface = small_font.render(move_text, True, (150, 150, 170))
            surface.blit(move_surface, (info_x, info_y + 220))
        else:
            move_text = f"手数: {move_count}"
            move_surface = font.render(move_text, True, Colors.TEXT_LIGHT)
            surface.blit(move_surface, (info_x, info_y + 35))
            
            black_capture_text = f"黑提子: {captures['B']}"
            white_capture_text = f"白提子: {captures['W']}"
            
            black_capture_surface = small_font.render(black_capture_text, True, Colors.TEXT_LIGHT)
            white_capture_surface = small_font.render(white_capture_text, True, Colors.TEXT_LIGHT)
            
            surface.blit(black_capture_surface, (info_x, info_y + 70))
            surface.blit(white_capture_surface, (info_x, info_y + 95))
    
    def draw_situation_eval(self, surface, win_rate, territory_est, info_x, info_y):
        font = get_chinese_font(24)
        title_font = get_chinese_font(26)
        
        self.draw_sidebar_panel(surface, info_x - 15, info_y - 15, 260, 110, "形势判断")
        
        info_x += 5
        info_y += 35
        
        title_surface = title_font.render("形势评估", True, Colors.GOLD)
        surface.blit(title_surface, (info_x, info_y - 5))
        
        if win_rate is not None:
            wr_text = f"黑胜率: {win_rate:.1%}"
            wr_color = Colors.GREEN if win_rate > 0.5 else Colors.RED if win_rate < 0.5 else Colors.TEXT_LIGHT
            wr_surface = font.render(wr_text, True, wr_color)
            surface.blit(wr_surface, (info_x, info_y + 20))
        
        if territory_est is not None:
            terr_text = f"黑{territory_est['black']}目 vs 白{territory_est['white']}目"
            terr_surface = font.render(terr_text, True, Colors.TEXT_LIGHT)
            surface.blit(terr_surface, (info_x, info_y + 45))
    
    def draw_ai_thinking(self, surface, x, y, width):
        font = get_chinese_font(24)
        
        dots = int((self.animation_time * 3) % 4)
        thinking_text = f"AI思考中{'.' * dots}"
        text_surface = font.render(thinking_text, True, Colors.GOLD_LIGHT)
        
        bg_rect = pygame.Rect(x, y, width, 40)
        pygame.draw.rect(surface, (40, 40, 50), bg_rect, border_radius=8)
        pygame.draw.rect(surface, Colors.GOLD, bg_rect, 1, border_radius=8)
        
        text_rect = text_surface.get_rect(center=bg_rect.center)
        surface.blit(text_surface, text_rect)
