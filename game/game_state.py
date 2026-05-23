from game.board import Board
from game.rules import Rules
import math
import pickle
import os


class GameState:
    def __init__(self, board_size=19):
        self.board_size = board_size
        self.board = Board(board_size)
        self.current_player = 'B'
        self.move_count = 0
        self.captures = {'B': 0, 'W': 0}
        self.ko_point = None
        self.history = []
        self.game_status = 'playing'
        self.rules = Rules()
        self.consecutive_passes = 0
        self.winner = None
        self.final_score = None
        self.moves_since_last_capture = 0
        self.moves_since_last_big_move = 0
        self.last_board_hash = None
        self.ko_history = []
        self.last_move = None
        self.move_history = []       # [(x, y, color), ...] — 走法序列
        self.redo_history = []       # 回顾模式前进用的快照
        self.review_index = -1       # 回顾模式当前步数索引，-1 表示不在回顾模式
        self.dead_stones = set()     # 被标记为死子的位置 {(x, y), ...}
    
    def get_board_hash(self):
        return self.board.get_state_hash()
    
    def make_move(self, x, y):
        if self.game_status != 'playing':
            return False
        
        # 超级劫检测：检查局面是否出现过
        if self._is_superko(x, y):
            return False
        
        if not self.rules.is_valid_move(self.board, x, y, self.current_player, self.ko_point):
            return False
        
        self.save_state()
        
        success, captured_count, new_ko_point = self.rules.place_stone(self.board, x, y, self.current_player, self.ko_point)
        
        if success:
            self.captures[self.current_player] += captured_count
            self.ko_point = new_ko_point
            self.move_count += 1
            
            if captured_count > 0:
                self.moves_since_last_capture = 0
            else:
                self.moves_since_last_capture += 1
            
            if self._is_big_move(x, y):
                self.moves_since_last_big_move = 0
            else:
                self.moves_since_last_big_move += 1
            
            moving_player = self.current_player
            self.current_player = 'W' if self.current_player == 'B' else 'B'
            self.consecutive_passes = 0

            # 记录最后落子位置和走法历史
            self.last_move = (x, y)
            self.move_history.append((x, y, moving_player))
            self.redo_history.clear()

            # 记录当前棋盘哈希
            self.ko_history.append(self.get_board_hash())
            
            if self._should_auto_end():
                self.end_game()
        
        return success
    
    def _is_superko(self, x, y):
        """
        检测是否是超级劫（局面重复）
        """
        if len(self.ko_history) < 2:
            return False
        
        test_board = self.board.copy()
        if self.rules.is_valid_move(test_board, x, y, self.current_player, self.ko_point):
            self.rules.place_stone(test_board, x, y, self.current_player, self.ko_point)
            test_hash = test_board.get_state_hash()
            if test_hash in self.ko_history:
                return True
        
        return False
    
    def _is_big_move(self, x, y):
        for dx in [-2, -1, 0, 1, 2]:
            for dy in [-2, -1, 0, 1, 2]:
                nx, ny = x + dx, y + dy
                if self.board.is_valid_position(nx, ny) and self.board.is_empty(nx, ny):
                    return True
        return False
    
    def _should_auto_end(self):
        if self.move_count < 30:
            return False
        
        if self.moves_since_last_capture > 60:
            return True
        
        if self.moves_since_last_big_move > 40:
            return True
        
        return False
    
    def pass_move(self):
        if self.game_status != 'playing':
            return False
        
        passing_player = self.current_player
        self.save_state()
        self.consecutive_passes += 1
        self.move_count += 1
        self.current_player = 'W' if self.current_player == 'B' else 'B'
        self.last_move = None  # PASS 清除最后落子
        self.move_history.append((None, None, passing_player))
        self.redo_history.clear()
        
        if self.consecutive_passes >= 2:
            self.begin_dead_marking()
        
        return True
    
    def end_game(self):
        self.game_status = 'ended'
        self.calculate_final_score()

    def begin_dead_marking(self):
        """进入死子标记模式（终局结算前）"""
        self.game_status = 'end_marking'
        self.dead_stones.clear()
    
    def mark_dead_stone(self, x, y):
        """标记/取消标记死子"""
        pos = (x, y)
        if pos in self.dead_stones:
            self.dead_stones.discard(pos)
        else:
            self.dead_stones.add(pos)

    def clear_dead_stones(self):
        """清除所有死子标记"""
        self.dead_stones.clear()

    def confirm_dead_stones(self):
        """确认死子标记并重新计算分数"""
        if not self.dead_stones:
            self.end_game()
            return
        # 从棋盘移除死子
        dead_by_color = {'B': 0, 'W': 0}
        for (x, y) in self.dead_stones:
            stone = self.board.get_stone(x, y)
            if stone:
                dead_by_color[stone] += 1
                self.board.set_stone(x, y, None)
        # 死子计入对方提子
        self.captures['B'] += dead_by_color['W']
        self.captures['W'] += dead_by_color['B']
        self.game_status = 'ended'
        self.calculate_final_score()

    def calculate_final_score(self):
        black_territory, white_territory = self.calculate_territory()

        black_stones = 0
        white_stones = 0
        for y in range(self.board.size):
            for x in range(self.board.size):
                stone = self.board.get_stone(x, y)
                if stone == 'B':
                    black_stones += 1
                elif stone == 'W':
                    white_stones += 1

        black_total = black_stones + black_territory + self.captures['B']
        white_total = white_stones + white_territory + self.captures['W'] + 3.75

        self.final_score = {
            'black': black_total,
            'white': white_total,
            'black_territory': black_territory,
            'white_territory': white_territory,
            'black_stones': black_stones,
            'white_stones': white_stones,
            'captures': self.captures.copy()
        }

        if black_total > white_total:
            self.winner = 'B'
        else:
            self.winner = 'W'
    
    def calculate_territory(self):
        visited = set()
        black_territory = 0
        white_territory = 0
        
        for y in range(self.board.size):
            for x in range(self.board.size):
                if (x, y) not in visited and self.board.is_empty(x, y):
                    territory, owner = self._flood_fill_territory(x, y, visited)
                    if owner == 'B':
                        black_territory += territory
                    elif owner == 'W':
                        white_territory += territory
        
        return black_territory, white_territory
    
    def _flood_fill_territory(self, start_x, start_y, visited):
        from collections import deque
        queue = deque()
        queue.append((start_x, start_y))
        
        territory = set()
        border_colors = set()
        all_adjacent_points = []
        
        while queue:
            x, y = queue.popleft()
            if (x, y) in territory:
                continue
            if not self.board.is_valid_position(x, y):
                continue
            
            stone = self.board.get_stone(x, y)
            if stone is not None:
                border_colors.add(stone)
                all_adjacent_points.append((x, y))
                continue
            
            territory.add((x, y))
            visited.add((x, y))
            
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                queue.append((x + dx, y + dy))
        
        owner = None
        if len(border_colors) == 1:
            owner = border_colors.pop()
        
        return len(territory), owner
    
    def calculate_influence_map(self):
        influence = [[0.0 for _ in range(self.board.size)] for _ in range(self.board.size)]
        
        for y in range(self.board.size):
            for x in range(self.board.size):
                stone = self.board.get_stone(x, y)
                if stone is not None:
                    sign = 1.0 if stone == 'B' else -1.0
                    for dy in range(self.board.size):
                        for dx in range(self.board.size):
                            distance = max(abs(x - dx), abs(y - dy))
                            if distance > 6:
                                continue
                            influence[dy][dx] += sign * (1.0 / (distance + 1))
        
        return influence
    
    def estimate_situation(self):
        """估算当前形势"""
        # 早期棋局使用影响力估算，后期使用领地计算
        black_territory, white_territory = self.calculate_territory()
        total_territory = black_territory + white_territory

        # 领地太少（开局阶段），回退到影响力估算
        if total_territory < 10 and self.move_count < 40:
            influence = self.calculate_influence_map()
            black_terr = 0
            white_terr = 0
            for y in range(self.board.size):
                for x in range(self.board.size):
                    if self.board.get_stone(x, y) is None:
                        inf = influence[y][x]
                        if inf > 0.3:
                            black_terr += 1
                        elif inf < -0.3:
                            white_terr += 1
            black_territory = max(black_territory, black_terr)
            white_territory = max(white_territory, white_terr)

        black_score = black_territory + self.captures['B']
        white_score = white_territory + self.captures['W'] + 7.5

        score_diff = black_score - white_score

        # 使用sigmoid函数估值胜率
        win_rate = 1.0 / (1.0 + math.exp(-score_diff / 5.0))

        return {
            'win_rate': round(win_rate, 3),
            'territory': {'black': black_territory, 'white': white_territory}
        }
    
    def undo(self):
        if len(self.history) == 0:
            return False

        snapshot = self.history.pop()
        self.load_state(snapshot)
        if self.move_history:
            self.move_history.pop()
        self.redo_history.clear()
        return True

    def go_to_move(self, target_index):
        """回顾模式：跳转到指定步数"""
        if target_index < 0 or target_index >= len(self.move_history):
            return False
        # 从初始状态开始重放到目标步
        temp_board = Board(self.board_size)
        temp_history = []
        for i in range(target_index + 1):
            mx, my, mc = self.move_history[i]
            if mx is not None:
                temp_history.append(temp_board.get_state_hash())
                temp_board.set_stone(mx, my, mc)

        # 将当前棋盘设为目标状态
        self.board = temp_board
        self.current_player = 'W' if self.move_history[target_index][2] == 'B' else 'B'
        self.last_move = (self.move_history[target_index][0], self.move_history[target_index][1])
        self.review_index = target_index
        return True

    def review_prev(self):
        """回顾模式：上一步"""
        new_idx = self.review_index - 1
        if new_idx < -1:
            return False
        if new_idx == -1:
            self.reset()
            self.review_index = -1
            return True
        return self.go_to_move(new_idx)

    def review_next(self):
        """回顾模式：下一步"""
        if self.review_index >= len(self.move_history) - 1:
            return False
        return self.go_to_move(self.review_index + 1)
    
    def reset(self):
        self.board = Board(self.board_size)
        self.current_player = 'B'
        self.move_count = 0
        self.captures = {'B': 0, 'W': 0}
        self.ko_point = None
        self.history = []
        self.game_status = 'playing'
        self.consecutive_passes = 0
        self.winner = None
        self.final_score = None
        self.moves_since_last_capture = 0
        self.moves_since_last_big_move = 0
        self.last_move = None
        self.ko_history = []
        self.move_history = []
        self.redo_history = []
        self.review_index = -1
        self.dead_stones = set()

    def save_state(self):
        snapshot = self.get_state_snapshot()
        self.history.append(snapshot)
    
    def get_state_snapshot(self):
        board_copy = self.board.copy()
        return {
            'board': board_copy,
            'current_player': self.current_player,
            'move_count': self.move_count,
            'captures': self.captures.copy(),
            'ko_point': self.ko_point,
            'game_status': self.game_status,
            'consecutive_passes': self.consecutive_passes,
            'winner': self.winner,
            'final_score': self.final_score,
            'ko_history': self.ko_history.copy(),
            'last_move': self.last_move,
            'board_size': self.board_size
        }

    def load_state(self, snapshot):
        self.board_size = snapshot.get('board_size', 19)
        self.board = snapshot['board'].copy()
        self.current_player = snapshot['current_player']
        self.move_count = snapshot['move_count']
        self.captures = snapshot['captures'].copy()
        self.ko_point = snapshot['ko_point']
        self.game_status = snapshot['game_status']
        self.consecutive_passes = snapshot.get('consecutive_passes', 0)
        self.winner = snapshot.get('winner', None)
        self.final_score = snapshot.get('final_score', None)
        self.ko_history = snapshot.get('ko_history', [])
        self.last_move = snapshot.get('last_move', None)
    
    def save_game(self, filename='data/saves/savegame.pkl'):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'wb') as f:
            pickle.dump(self.get_state_snapshot(), f)
    
    def load_game(self, filename='data/saves/savegame.pkl'):
        if not os.path.exists(filename):
            return False
        with open(filename, 'rb') as f:
            snapshot = pickle.load(f)
        self.load_state(snapshot)
        return True
