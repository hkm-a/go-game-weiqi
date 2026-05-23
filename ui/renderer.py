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
    def __init__(self, screen, board_x, board_y, board_size, grid_size=19):
        self.screen = screen
        self.board_x = board_x
        self.board_y = board_y
        self.board_size = board_size
        self.board_width = board_size
        self.board_height = board_size
        self.grid_size = grid_size
        self.cell_size = (self.board_width - 100) // (self.grid_size - 1)
        self.stone_radius = max(8, self.cell_size // 2 - 4)
        self.star_point_radius = max(3, self.cell_size // 16)

        self.animation_time = 0
        self.particles = []

        # 根据棋盘大小选择星位
        if grid_size == 19:
            self.star_points = [
                (3, 3), (3, 9), (3, 15),
                (9, 3), (9, 9), (9, 15),
                (15, 3), (15, 9), (15, 15)
            ]
        elif grid_size == 13:
            self.star_points = [
                (3, 3), (3, 6), (3, 9),
                (6, 3), (6, 6), (6, 9),
                (9, 3), (9, 6), (9, 9)
            ]
        elif grid_size == 9:
            self.star_points = [
                (2, 2), (2, 6), (4, 4),
                (6, 2), (6, 6)
            ]
        else:
            self.star_points = []

        self.board_texture = self._generate_board_texture()
        self._overlay_buttons = {}
    
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
    
    def draw_coordinates(self, surface):
        """绘制棋盘坐标标签 (A-T, 1-19)"""
        start_x = self.board_x + 50
        start_y = self.board_y + 50
        font = get_chinese_font(18)

        # 列标签 A-T (跳过 I)
        for i in range(self.grid_size):
            label = chr(ord('A') + i) if i < 8 else chr(ord('A') + i + 1)
            x = start_x + i * self.cell_size
            coord_surface = font.render(label, True, Colors.GOLD)
            coord_rect = coord_surface.get_rect(center=(x, start_y - 30))
            surface.blit(coord_surface, coord_rect)
            coord_rect = coord_surface.get_rect(center=(x, start_y + (self.grid_size - 1) * self.cell_size + 30))
            surface.blit(coord_surface, coord_rect)

        # 行标签 1-19
        for i in range(self.grid_size):
            label = str(self.grid_size - i)
            y = start_y + i * self.cell_size
            coord_surface = font.render(label, True, Colors.GOLD)
            coord_rect = coord_surface.get_rect(center=(start_x - 30, y))
            surface.blit(coord_surface, coord_rect)
            coord_rect = coord_surface.get_rect(center=(start_x + (self.grid_size - 1) * self.cell_size + 30, y))
            surface.blit(coord_surface, coord_rect)

    def draw_last_move(self, surface, last_move):
        """绘制最后落子标记"""
        if last_move is None:
            return
        screen_pos = self.board_to_screen(last_move[0], last_move[1])
        if screen_pos is None:
            return
        cx, cy = screen_pos
        marker_size = self.stone_radius // 3
        pygame.draw.circle(surface, (255, 80, 80), (cx, cy), marker_size)

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
    
    def draw_current_player(self, surface, current_player, move_count, captures, game_status=None, winner=None, final_score=None, info_y=None, info_x=None, panel_width=360, panel_height=None):
        font = get_chinese_font(28)
        small_font = get_chinese_font(24)

        if info_x is None:
            info_x = self.board_x + self.board_width + 50
        if info_y is None:
            info_y = self.board_y + 30

        if panel_height is None:
            panel_height = 300 if game_status == 'ended' else 200

        self.draw_sidebar_panel(surface, info_x, info_y, panel_width, panel_height, "游戏状态")

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
    
    def draw_situation_eval(self, surface, win_rate, territory_est, info_x, info_y, panel_width=360, panel_height=110):
        big_font = get_chinese_font(28)
        small_font = get_chinese_font(24)

        self.draw_sidebar_panel(surface, info_x, info_y, panel_width, panel_height, "形势判断")

        info_x += 5
        info_y += 35

        if win_rate is not None:
            wr_text = f"黑胜率: {win_rate:.1%}"
            wr_color = Colors.GREEN if win_rate > 0.5 else Colors.RED if win_rate < 0.5 else Colors.TEXT_LIGHT
            wr_surface = big_font.render(wr_text, True, wr_color)
            surface.blit(wr_surface, (info_x, info_y))

        if territory_est is not None:
            terr_text = f"黑{territory_est['black']}目 vs 白{territory_est['white']}目"
            terr_surface = small_font.render(terr_text, True, Colors.TEXT_LIGHT)
            surface.blit(terr_surface, (info_x, info_y + 35))
    
    def draw_timer(self, surface, player_times, info_x, info_y, panel_width=360):
        """绘制双方用时"""
        font = get_chinese_font(22)
        self.draw_sidebar_panel(surface, info_x, info_y, panel_width, 65, "计时")
        y = info_y + 35
        for i, (color, label) in enumerate([('B', '黑方'), ('W', '白方')]):
            remaining = max(0, int(player_times[color]))
            mins, secs = divmod(remaining, 60)
            time_str = f"{label}: {mins:02d}:{secs:02d}"
            is_low = remaining < 30
            color_val = (255, 80, 80) if is_low else (200, 200, 210)
            s = font.render(time_str, True, color_val)
            x = info_x + 20 + i * 178  # 均分360px宽
            surface.blit(s, (x, y))

    def draw_ai_thinking(self, surface, x, y, width, elapsed=0):
        font = get_chinese_font(24)
        small_font = get_chinese_font(18)

        dots = int((self.animation_time * 3) % 4)
        thinking_text = f"AI思考中{'.' * dots}"
        text_surface = font.render(thinking_text, True, Colors.GOLD_LIGHT)

        bg_rect = pygame.Rect(x, y, width, 55)
        pygame.draw.rect(surface, (40, 40, 50), bg_rect, border_radius=8)
        pygame.draw.rect(surface, Colors.GOLD, bg_rect, 1, border_radius=8)

        text_rect = text_surface.get_rect(center=(bg_rect.centerx, bg_rect.centery - 8))
        surface.blit(text_surface, text_rect)

        if elapsed:
            time_text = f"{elapsed:.1f}s"
            time_surface = small_font.render(time_text, True, (180, 180, 190))
            time_rect = time_surface.get_rect(center=(bg_rect.centerx, bg_rect.centery + 18))
            surface.blit(time_surface, time_rect)

    def draw_game_over_overlay(self, surface, winner, final_score, move_count):
        """绘制终局弹窗"""
        w, h = surface.get_width(), surface.get_height()
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        # 面板尺寸
        pw, ph = 480, 380
        px, py = (w - pw) // 2, (h - ph) // 2
        pygame.draw.rect(surface, (28, 28, 40), (px, py, pw, ph), border_radius=16)
        pygame.draw.rect(surface, Colors.GOLD, (px, py, pw, ph), 2, border_radius=16)

        tf = get_chinese_font(30)
        sf = get_chinese_font(22)
        ssf = get_chinese_font(18)

        # 标题
        title = "游戏结束" if winner else "平局"
        ts = tf.render(title, True, Colors.GOLD_LIGHT)
        surface.blit(ts, (px + 30, py + 25))

        # 分隔线
        pygame.draw.line(surface, (60, 60, 75), (px + 30, py + 65), (px + pw - 30, py + 65), 1)

        # 获胜者徽章
        if winner:
            wt = "黑方 获胜" if winner == 'B' else "白方 获胜"
            ws = sf.render(wt, True, Colors.GOLD_LIGHT)
            badge = pygame.Rect(0, 0, 160, 36)
            badge.center = (px + pw // 2, py + 100)
            pygame.draw.rect(surface, (50, 50, 65), badge, border_radius=18)
            pygame.draw.rect(surface, Colors.GOLD, badge, 1, border_radius=18)
            surface.blit(ws, ws.get_rect(center=badge.center))

        # 分数表
        if final_score:
            col_x = [px + 60, px + 240, px + 360]
            row_y = py + 135
            f = ssf
            labels = ["棋子", "领地", "小计"]
            black_vals = [
                str(final_score.get('black_stones', 0)),
                str(final_score.get('black_territory', 0)),
                str(final_score.get('black_stones', 0) + final_score.get('black_territory', 0)),
            ]
            white_vals = [
                str(final_score.get('white_stones', 0)),
                str(final_score.get('white_territory', 0)),
                str(final_score.get('white_stones', 0) + final_score.get('white_territory', 0)),
            ]

            # 表头
            for txt, cx in [("项目", col_x[0]), ("黑方", col_x[1]), ("白方", col_x[2])]:
                surface.blit(f.render(txt, True, (160, 160, 180)), (cx, row_y))

            # 分隔线
            pygame.draw.line(surface, (50, 50, 65), (px + 50, row_y + 28), (px + pw - 50, row_y + 28), 1)

            # 数据行
            for i in range(3):
                ry = row_y + 35 + i * 28
                surface.blit(f.render(labels[i], True, (190, 190, 200)), (col_x[0], ry))
                surface.blit(f.render(black_vals[i], True, (210, 210, 220)), (col_x[1], ry))
                surface.blit(f.render(white_vals[i], True, (210, 210, 220)), (col_x[2], ry))

            # 贴目
            ry = row_y + 35 + 3 * 28
            surface.blit(f.render("贴目", True, (190, 190, 200)), (col_x[0], ry))
            surface.blit(f.render("+3.75", True, (210, 210, 220)), (col_x[2], ry))

            # 分隔线
            pygame.draw.line(surface, (60, 60, 75), (px + 50, ry + 32), (px + pw - 50, ry + 32), 1)

            # 总分
            ry += 40
            surface.blit(sf.render("总分", True, Colors.GOLD_LIGHT), (col_x[0], ry))
            surface.blit(sf.render(f"{final_score.get('black', 0):.1f}", True, Colors.GOLD_LIGHT), (col_x[1], ry))
            surface.blit(sf.render(f"{final_score.get('white', 0):.1f}", True, Colors.GOLD_LIGHT), (col_x[2], ry))

        # 按钮
        by = py + ph - 55
        btn_w, btn_h = 140, 38
        mx = px + pw // 2
        restart_rect = pygame.Rect(mx - btn_w - 10, by, btn_w, btn_h)
        review_rect = pygame.Rect(mx + 10, by, btn_w, btn_h)

        for rect, label, color in [(restart_rect, "重新开始", Colors.GOLD),
                                    (review_rect, "复盘", Colors.GOLD)]:
            hovered = rect.collidepoint(pygame.mouse.get_pos())
            bg = (55, 55, 70) if hovered else (45, 45, 60)
            bc = Colors.GOLD_LIGHT if hovered else color
            pygame.draw.rect(surface, bg, rect, border_radius=8)
            pygame.draw.rect(surface, bc, rect, 2, border_radius=8)
            txt = sf.render(label, True, Colors.GOLD_LIGHT)
            surface.blit(txt, txt.get_rect(center=rect.center))

        self._overlay_buttons = {'restart': restart_rect, 'review': review_rect}

    def draw_territory_overlay(self, surface, final_score, board):
        """在棋盘上绘制领地区域"""
        if not final_score:
            return
        start_x = self.board_x + 50
        start_y = self.board_y + 50
        from game.game_state import GameState
        gs = GameState()
        gs.board = board
        black_territory, white_territory = gs.calculate_territory()
        # 为了可视化，重新执行flood fill获取具体位置
        visited = set()
        territory_positions = {'B': [], 'W': []}
        for y in range(board.size):
            for x in range(board.size):
                if (x, y) not in visited and board.is_empty(x, y):
                    terr_set = set()
                    border_colors = set()
                    stack = [(x, y)]
                    while stack:
                        cx, cy = stack.pop()
                        if (cx, cy) in visited or not board.is_valid_position(cx, cy):
                            continue
                        stone = board.get_stone(cx, cy)
                        if stone is not None:
                            border_colors.add(stone)
                            continue
                        if (cx, cy) in terr_set:
                            continue
                        terr_set.add((cx, cy))
                        visited.add((cx, cy))
                        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            stack.append((cx + dx, cy + dy))
                    if len(border_colors) == 1:
                        owner = border_colors.pop()
                        territory_positions[owner].extend(list(terr_set))

        for color, positions in territory_positions.items():
            fill_color = (80, 120, 255, 60) if color == 'B' else (255, 100, 100, 60)
            for (tx, ty) in positions:
                cx = start_x + tx * self.cell_size
                cy = start_y + ty * self.cell_size
                s = pygame.Surface((self.cell_size, self.cell_size), pygame.SRCALPHA)
                pygame.draw.rect(s, fill_color, (0, 0, self.cell_size, self.cell_size), border_radius=2)
                surface.blit(s, (cx - self.cell_size // 2, cy - self.cell_size // 2))

    def draw_dead_stone_markers(self, surface, dead_stones):
        """在死子上绘制红色 X 标记"""
        for (x, y) in dead_stones:
            screen_pos = self.board_to_screen(x, y)
            if screen_pos is None:
                continue
            cx, cy = screen_pos
            size = self.stone_radius - 2
            color = (255, 50, 50)
            thickness = max(2, self.stone_radius // 6)
            pygame.draw.line(surface, color, (cx - size, cy - size), (cx + size, cy + size), thickness)
            pygame.draw.line(surface, color, (cx + size, cy - size), (cx - size, cy + size), thickness)

    def draw_review_overlay(self, surface, move_history, current_index, info_y, sidebar_x):
        """绘制复盘界面：步数导航 + 历史列表"""
        font = get_chinese_font(24)
        small_font = get_chinese_font(20)

        # 顶部提示条
        bar = pygame.Rect(0, 0, surface.get_width(), 50)
        pygame.draw.rect(surface, (30, 30, 45), bar)
        pygame.draw.rect(surface, (212, 175, 55), bar, 2)

        total = len(move_history)
        text = font.render(f"复盘模式 — 第 {current_index + 1}/{total} 手", True, (255, 223, 128))
        text_rect = text.get_rect(center=(surface.get_width() // 2, 25))
        surface.blit(text, text_rect)

        # 步数滑块
        slider_x, slider_y = 200, surface.get_height() - 40
        slider_w = surface.get_width() - 400
        pygame.draw.line(surface, (100, 100, 120), (slider_x, slider_y), (slider_x + slider_w, slider_y), 3)
        if total > 1:
            progress = current_index / (total - 1)
            dot_x = int(slider_x + progress * slider_w)
            pygame.draw.circle(surface, (255, 223, 128), (dot_x, slider_y), 10)

        # 侧边历史面板
        panel_x = sidebar_x
        panel_y = info_y - 15
        panel_w = 260
        panel_h = 200
        self.draw_sidebar_panel(surface, panel_x, panel_y, panel_w, panel_h, "走法历史")

        start_idx = max(0, current_index - 7)
        end_idx = min(total, start_idx + 9)
        y_off = panel_y + 40
        for i in range(start_idx, end_idx):
            mx, my, mc = move_history[i]
            if mx is None:
                move_text = f"{'B' if mc == 'B' else 'W'} PASS"
            else:
                col = chr(ord('A') + mx) if mx < 8 else chr(ord('A') + mx + 1)
                row = self.grid_size - my
                move_text = f"{'B' if mc == 'B' else 'W'}  {col}{row}"
            color = (255, 223, 128) if i == current_index else (200, 200, 200)
            bg_color = (50, 50, 65) if i == current_index else None
            if bg_color:
                pygame.draw.rect(surface, bg_color, (panel_x + 10, y_off - 2, panel_w - 20, 22), border_radius=4)
            label = small_font.render(f"{i+1}. {move_text}", True, color)
            surface.blit(label, (panel_x + 15, y_off))
            y_off += 22
