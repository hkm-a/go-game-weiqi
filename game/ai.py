import random
import time
import math
from typing import List, Tuple, Optional


class AI:
    def get_move(self, board, color, rules, ko_point=None) -> Optional[Tuple[int, int]]:
        raise NotImplementedError()
    
    def evaluate_position(self, board, color):
        raise NotImplementedError()


class EasyAI(AI):
    def __init__(self):
        self.opening_points = [
            (3, 3), (3, 9), (3, 15),
            (9, 3), (9, 9), (9, 15),
            (15, 3), (15, 9), (15, 15)
        ]
    
    def get_all_valid_moves(self, board, color, rules, ko_point=None) -> List[Tuple[int, int]]:
        valid_moves = []
        for y in range(board.size):
            for x in range(board.size):
                if rules.is_valid_move(board, x, y, color, ko_point):
                    valid_moves.append((x, y))
        return valid_moves
    
    def find_capturing_moves(self, board, color, rules, ko_point=None) -> List[Tuple[int, int]]:
        opponent = 'W' if color == 'B' else 'B'
        capturing_moves = []
        
        all_groups = board.get_all_groups()
        
        for group in all_groups:
            if board.get_stone(group[0][0], group[0][1]) != opponent:
                continue
            liberties = board.get_liberties(group)
            if liberties == 1:
                for y in range(board.size):
                    for x in range(board.size):
                        if board.is_empty(x, y):
                            test_board = board.copy()
                            test_board.set_stone(x, y, color)
                            captures = rules.check_captures(test_board, x, y, color)
                            if captures and any(group_to_check == group for group_to_check in captures):
                                if rules.is_valid_move(board, x, y, color, ko_point):
                                    if (x, y) not in capturing_moves:
                                        capturing_moves.append((x, y))
        
        if not capturing_moves:
            for y in range(board.size):
                for x in range(board.size):
                    if board.is_empty(x, y) and rules.is_valid_move(board, x, y, color, ko_point):
                        test_board = board.copy()
                        test_board.set_stone(x, y, color)
                        captures = rules.check_captures(test_board, x, y, color)
                        if captures:
                            if (x, y) not in capturing_moves:
                                capturing_moves.append((x, y))
        
        return capturing_moves
    
    def find_defensive_moves(self, board, color, rules, ko_point=None) -> List[Tuple[int, int]]:
        defensive_moves = []
        all_groups = board.get_all_groups()
        
        for group in all_groups:
            if board.get_stone(group[0][0], group[0][1]) != color:
                continue
            liberties = board.get_liberties(group)
            if liberties == 1:
                for y in range(board.size):
                    for x in range(board.size):
                        if board.is_empty(x, y):
                            test_board = board.copy()
                            test_board.set_stone(x, y, color)
                            new_group = test_board.get_group(x, y)
                            new_liberties = test_board.get_liberties(new_group)
                            if new_liberties > 1:
                                if rules.is_valid_move(board, x, y, color, ko_point):
                                    if (x, y) not in defensive_moves:
                                        defensive_moves.append((x, y))
        return defensive_moves
    
    def find_opening_moves(self, board) -> List[Tuple[int, int]]:
        opening_moves = []
        for x, y in self.opening_points:
            if board.is_empty(x, y):
                opening_moves.append((x, y))
        return opening_moves
    
    def get_move(self, board, color, rules, ko_point=None) -> Optional[Tuple[int, int]]:
        valid_moves = self.get_all_valid_moves(board, color, rules, ko_point)
        
        if not valid_moves:
            return None
        
        capturing_moves = self.find_capturing_moves(board, color, rules, ko_point)
        if capturing_moves:
            return random.choice(capturing_moves)
        
        defensive_moves = self.find_defensive_moves(board, color, rules, ko_point)
        if defensive_moves:
            return random.choice(defensive_moves)
        
        opening_moves = self.find_opening_moves(board)
        if opening_moves:
            return random.choice(opening_moves)
        
        return random.choice(valid_moves)
    
    def evaluate_position(self, board, color):
        opponent = 'W' if color == 'B' else 'B'
        score = 0
        
        all_groups = board.get_all_groups()
        
        for group in all_groups:
            group_color = board.get_stone(group[0][0], group[0][1])
            group_size = len(group)
            
            if group_color == color:
                score += group_size * 2
            else:
                score -= group_size * 2
        
        return score
    
    def get_best_moves_with_scores(self, board, color, rules, ko_point=None):
        valid_moves = self.get_all_valid_moves(board, color, rules, ko_point)
        if not valid_moves:
            return []
        
        move_scores = []
        for move in valid_moves:
            test_board = board.copy()
            rules.place_stone(test_board, move[0], move[1], color, ko_point)
            score = self.evaluate_position(test_board, color)
            move_scores.append((move, score))
        
        move_scores.sort(key=lambda x: x[1], reverse=True)
        return move_scores[:10]


class MediumAI(AI):
    def __init__(self):
        self.opening_points = [
            (3, 3), (3, 9), (3, 15),
            (9, 3), (9, 9), (9, 15),
            (15, 3), (15, 9), (15, 15)
        ]
        self.max_depth = 3
        self.time_limit = 2.5
        self.start_time = 0
    
    def get_position_value(self, x, y, board_size):
        center = board_size // 2
        dx = abs(x - center)
        dy = abs(y - center)
        distance = max(dx, dy)
        
        if distance == 0:
            return 10
        elif distance <= 2:
            return 8
        elif distance <= 4:
            return 6
        elif distance <= 6:
            return 4
        else:
            return 2
    
    def evaluate_position(self, board, color):
        opponent = 'W' if color == 'B' else 'B'
        score = 0
        
        all_groups = board.get_all_groups()
        
        for group in all_groups:
            group_color = board.get_stone(group[0][0], group[0][1])
            group_size = len(group)
            liberties = board.get_liberties(group)
            
            if group_color == color:
                score += group_size * 2
                
                if liberties >= 3:
                    score += 10
                elif liberties == 2:
                    score += 5
                elif liberties == 1:
                    score -= 20
                
                for (x, y) in group:
                    score += self.get_position_value(x, y, board.size)
            else:
                score -= group_size * 2
                
                if liberties >= 3:
                    score -= 10
                elif liberties == 2:
                    score -= 5
                elif liberties == 1:
                    score += 20
        
        for y in range(board.size):
            for x in range(board.size):
                if board.is_empty(x, y):
                    continue
                stone_color = board.get_stone(x, y)
                neighbors = 0
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if board.is_valid_position(nx, ny) and board.get_stone(nx, ny) == stone_color:
                        neighbors += 1
                if stone_color == color:
                    score += neighbors * 0.5
                else:
                    score -= neighbors * 0.5
        
        return score
    
    def get_candidate_moves(self, board, color, rules, ko_point=None) -> List[Tuple[int, int]]:
        candidates = []
        opponent = 'W' if color == 'B' else 'B'
        
        all_groups = board.get_all_groups()
        interesting_positions = set()
        
        for group in all_groups:
            liberties = board.get_liberties(group)
            group_color = board.get_stone(group[0][0], group[0][1])
            if liberties <= 3:
                for (x, y) in group:
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nx, ny = x + dx, y + dy
                        if board.is_valid_position(nx, ny) and board.is_empty(nx, ny):
                            interesting_positions.add((nx, ny))
        
        for y in range(board.size):
            for x in range(board.size):
                if board.is_empty(x, y):
                    has_neighbor = False
                    for dx in [-2, -1, 0, 1, 2]:
                        for dy in [-2, -1, 0, 1, 2]:
                            if dx == 0 and dy == 0:
                                continue
                            nx, ny = x + dx, y + dy
                            if board.is_valid_position(nx, ny) and not board.is_empty(nx, ny):
                                has_neighbor = True
                                break
                        if has_neighbor:
                            break
                    if has_neighbor:
                        interesting_positions.add((x, y))
        
        for x, y in self.opening_points:
            if board.is_empty(x, y):
                interesting_positions.add((x, y))
        
        for x, y in interesting_positions:
            if rules.is_valid_move(board, x, y, color, ko_point):
                candidates.append((x, y))
        
        if not candidates:
            for y in range(board.size):
                for x in range(board.size):
                    if rules.is_valid_move(board, x, y, color, ko_point):
                        candidates.append((x, y))
        
        return candidates[:30]
    
    def minimax(self, board, color, rules, ko_point, depth, alpha, beta, is_maximizing, original_color):
        if time.time() - self.start_time > self.time_limit:
            return self.evaluate_position(board, original_color), None
        
        if depth == 0:
            return self.evaluate_position(board, original_color), None
        
        opponent = 'W' if color == 'B' else 'B'
        valid_moves = self.get_candidate_moves(board, color, rules, ko_point)
        
        if not valid_moves:
            return self.evaluate_position(board, original_color), None
        
        best_move = None
        
        if is_maximizing:
            max_eval = -float('inf')
            for move in valid_moves:
                test_board = board.copy()
                test_board.set_stone(move[0], move[1], color)
                rules.check_captures(test_board, move[0], move[1], color)
                new_ko_point = move if rules.is_ko(test_board, move[0], move[1], color) else None
                
                eval_score, _ = self.minimax(test_board, opponent, rules, new_ko_point, depth - 1, alpha, beta, False, original_color)
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for move in valid_moves:
                test_board = board.copy()
                test_board.set_stone(move[0], move[1], color)
                rules.check_captures(test_board, move[0], move[1], color)
                new_ko_point = move if rules.is_ko(test_board, move[0], move[1], color) else None
                
                eval_score, _ = self.minimax(test_board, opponent, rules, new_ko_point, depth - 1, alpha, beta, True, original_color)
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            
            return min_eval, best_move
    
    def get_move(self, board, color, rules, ko_point=None) -> Optional[Tuple[int, int]]:
        self.start_time = time.time()
        
        all_valid = []
        for y in range(board.size):
            for x in range(board.size):
                if rules.is_valid_move(board, x, y, color, ko_point):
                    all_valid.append((x, y))
        
        if not all_valid:
            return None
        
        opponent = 'W' if color == 'B' else 'B'
        for x, y in all_valid:
            test_board = board.copy()
            test_board.set_stone(x, y, color)
            captures = rules.check_captures(test_board, x, y, color)
            if captures:
                total_captured = sum(len(g) for g in captures)
                if total_captured >= 2:
                    return (x, y)
        
        all_groups = board.get_all_groups()
        for group in all_groups:
            if board.get_stone(group[0][0], group[0][1]) == color:
                liberties = board.get_liberties(group)
                if liberties == 1:
                    for x, y in all_valid:
                        test_board = board.copy()
                        test_board.set_stone(x, y, color)
                        new_group = test_board.get_group(x, y)
                        if new_group:
                            new_liberties = test_board.get_liberties(new_group)
                            if new_liberties > 1:
                                return (x, y)
        
        _, best_move = self.minimax(board, color, rules, ko_point, self.max_depth, -float('inf'), float('inf'), True, color)
        
        if best_move is not None:
            return best_move
        
        return random.choice(all_valid)
    
    def get_best_moves_with_scores(self, board, color, rules, ko_point=None):
        valid_moves = self.get_candidate_moves(board, color, rules, ko_point)
        if not valid_moves:
            return []
        
        move_scores = []
        for move in valid_moves:
            test_board = board.copy()
            rules.place_stone(test_board, move[0], move[1], color, ko_point)
            score = self.evaluate_position(test_board, color)
            move_scores.append((move, score))
        
        move_scores.sort(key=lambda x: x[1], reverse=True)
        return move_scores[:10]


class MCTSNode:
    def __init__(self, board, color, rules, ko_point, parent=None, move=None):
        self.board = board
        self.color = color
        self.rules = rules
        self.ko_point = ko_point
        self.parent = parent
        self.move = move
        self.children = []
        self.wins = 0
        self.visits = 0
        self.untried_moves = self._get_valid_moves()
    
    def _get_valid_moves(self):
        moves = []
        for y in range(self.board.size):
            for x in range(self.board.size):
                if self.rules.is_valid_move(self.board, x, y, self.color, self.ko_point):
                    moves.append((x, y))
        return moves
    
    def is_fully_expanded(self):
        return len(self.untried_moves) == 0
    
    def is_terminal(self):
        return len(self.untried_moves) == 0
    
    def select_child(self, c_param=1.4):
        choices_weights = [
            (child.wins / child.visits) + c_param * math.sqrt((2 * math.log(self.visits) / child.visits))
            for child in self.children
        ]
        return self.children[choices_weights.index(max(choices_weights))]
    
    def expand(self):
        move = self.untried_moves.pop(random.randint(0, len(self.untried_moves) - 1))
        new_board = self.board.copy()
        new_ko_point = self.rules.place_stone(new_board, move[0], move[1], self.color, self.ko_point)[2]
        next_color = 'W' if self.color == 'B' else 'B'
        child_node = MCTSNode(new_board, next_color, self.rules, new_ko_point, self, move)
        self.children.append(child_node)
        return child_node
    
    def simulate(self, original_color, max_steps=50):
        board_copy = self.board.copy()
        current_color = self.color
        current_ko = self.ko_point
        steps = 0
        
        while steps < max_steps:
            valid_moves = []
            for y in range(board_copy.size):
                for x in range(board_copy.size):
                    if self.rules.is_valid_move(board_copy, x, y, current_color, current_ko):
                        valid_moves.append((x, y))
            
            if not valid_moves:
                break
            
            move = random.choice(valid_moves)
            current_ko = self.rules.place_stone(board_copy, move[0], move[1], current_color, current_ko)[2]
            current_color = 'W' if current_color == 'B' else 'B'
            steps += 1
        
        score = self._evaluate_simulation(board_copy, original_color)
        return score
    
    def _evaluate_simulation(self, board, original_color):
        opponent = 'W' if original_color == 'B' else 'B'
        score = 0
        
        all_groups = board.get_all_groups()
        
        for group in all_groups:
            group_color = board.get_stone(group[0][0], group[0][1])
            group_size = len(group)
            liberties = board.get_liberties(group)
            
            if group_color == original_color:
                score += group_size * 2
                if liberties >= 3:
                    score += 5
                elif liberties == 1:
                    score -= 10
            else:
                score -= group_size * 2
                if liberties >= 3:
                    score -= 5
                elif liberties == 1:
                    score += 10
        
        return 1 if score > 0 else 0 if score < 0 else 0.5
    
    def backpropagate(self, result):
        self.visits += 1
        self.wins += result
        if self.parent:
            self.parent.backpropagate(1 - result)


class HardAI(AI):
    def __init__(self):
        self.time_limit = 8.0
        self.opening_points = [
            (3, 3), (3, 9), (3, 15),
            (9, 3), (9, 9), (9, 15),
            (15, 3), (15, 9), (15, 15)
        ]
    
    def evaluate_position(self, board, color):
        opponent = 'W' if color == 'B' else 'B'
        score = 0
        
        all_groups = board.get_all_groups()
        
        for group in all_groups:
            group_color = board.get_stone(group[0][0], group[0][1])
            group_size = len(group)
            liberties = board.get_liberties(group)
            
            if group_color == color:
                score += group_size * 3
                if liberties >= 3:
                    score += 15
                elif liberties == 2:
                    score += 8
                elif liberties == 1:
                    score -= 30
            else:
                score -= group_size * 3
                if liberties >= 3:
                    score -= 15
                elif liberties == 2:
                    score -= 8
                elif liberties == 1:
                    score += 30
        
        for y in range(board.size):
            for x in range(board.size):
                if board.is_empty(x, y):
                    continue
                stone_color = board.get_stone(x, y)
                neighbors = 0
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if board.is_valid_position(nx, ny) and board.get_stone(nx, ny) == stone_color:
                        neighbors += 1
                if stone_color == color:
                    score += neighbors * 0.8
                else:
                    score -= neighbors * 0.8
        
        return score
    
    def get_candidate_moves(self, board, color, rules, ko_point=None):
        candidates = []
        interesting_positions = set()
        
        all_groups = board.get_all_groups()
        for group in all_groups:
            liberties = board.get_liberties(group)
            if liberties <= 3:
                for (x, y) in group:
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nx, ny = x + dx, y + dy
                        if board.is_valid_position(nx, ny) and board.is_empty(nx, ny):
                            interesting_positions.add((nx, ny))
        
        for y in range(board.size):
            for x in range(board.size):
                if board.is_empty(x, y):
                    has_neighbor = False
                    for dx in [-2, -1, 0, 1, 2]:
                        for dy in [-2, -1, 0, 1, 2]:
                            if dx == 0 and dy == 0:
                                continue
                            nx, ny = x + dx, y + dy
                            if board.is_valid_position(nx, ny) and not board.is_empty(nx, ny):
                                has_neighbor = True
                                break
                        if has_neighbor:
                            break
                    if has_neighbor:
                        interesting_positions.add((x, y))
        
        for x, y in self.opening_points:
            if board.is_empty(x, y):
                interesting_positions.add((x, y))
        
        for x, y in interesting_positions:
            if rules.is_valid_move(board, x, y, color, ko_point):
                candidates.append((x, y))
        
        if not candidates:
            for y in range(board.size):
                for x in range(board.size):
                    if rules.is_valid_move(board, x, y, color, ko_point):
                        candidates.append((x, y))
        
        return candidates[:20]
    
    def get_best_moves_with_scores(self, board, color, rules, ko_point=None):
        all_valid = self.get_candidate_moves(board, color, rules, ko_point)
        if not all_valid:
            return []
        
        move_scores = []
        for move in all_valid:
            test_board = board.copy()
            test_ko = rules.place_stone(test_board, move[0], move[1], color, ko_point)[2]
            score = self.evaluate_position(test_board, color)
            move_scores.append((move, score))
        
        move_scores.sort(key=lambda x: x[1], reverse=True)
        return move_scores
    
    def get_move(self, board, color, rules, ko_point=None) -> Optional[Tuple[int, int]]:
        start_time = time.time()
        
        all_valid = self.get_candidate_moves(board, color, rules, ko_point)
        if not all_valid:
            return None
        
        for x, y in all_valid:
            test_board = board.copy()
            test_board.set_stone(x, y, color)
            captures = rules.check_captures(test_board, x, y, color)
            if captures:
                total_captured = sum(len(g) for g in captures)
                if total_captured >= 3:
                    return (x, y)
        
        all_groups = board.get_all_groups()
        for group in all_groups:
            if board.get_stone(group[0][0], group[0][1]) == color:
                liberties = board.get_liberties(group)
                if liberties == 1:
                    for x, y in all_valid:
                        test_board = board.copy()
                        test_board.set_stone(x, y, color)
                        new_group = test_board.get_group(x, y)
                        if new_group:
                            new_liberties = test_board.get_liberties(new_group)
                            if new_liberties > 1:
                                return (x, y)
        
        root = MCTSNode(board.copy(), color, rules, ko_point)
        
        while time.time() - start_time < self.time_limit:
            node = root
            
            while node.is_fully_expanded() and not node.is_terminal():
                node = node.select_child()
            
            if not node.is_fully_expanded():
                node = node.expand()
            
            result = node.simulate(color)
            node.backpropagate(result)
        
        if root.children:
            best_child = max(root.children, key=lambda c: c.visits)
            return best_child.move
        
        return random.choice(all_valid)
