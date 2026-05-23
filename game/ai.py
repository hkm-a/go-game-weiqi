import random
import time
import math
from typing import List, Tuple, Optional


class AI:
    def get_move(self, board, color, rules, ko_point=None) -> Optional[Tuple[int, int]]:
        raise NotImplementedError()
    
    def evaluate_position(self, board, color):
        raise NotImplementedError()
    
    def find_ko_threats(self, board, color, ko_point, rules):
        """
        寻找劫材
        
        Args:
            board: 当前棋盘
            color: AI颜色
            ko_point: 劫点位置
            rules: 规则对象
        
        Returns:
            劫材位置列表，按威胁程度排序
        """
        from game.ko_utils import KoUtils
        
        if ko_point is None:
            return []
        
        threats = KoUtils.find_ko_threats(board, color)
        
        threats = [pos for pos in threats if pos != ko_point]
        
        return threats


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

        if ko_point is not None:
            ko_threats = self.find_ko_threats(board, color, ko_point, rules)
            if ko_threats:
                # 选择威胁最大的劫材
                from game.ko_utils import KoUtils
                best = max(ko_threats, key=lambda pos: KoUtils._evaluate_ko_threat(board, pos[0], pos[1], color))
                return best

        # 优先吃子 - 选择能吃掉最多子的位置
        capturing_moves = self.find_capturing_moves(board, color, rules, ko_point)
        if capturing_moves:
            scored = []
            for move in capturing_moves:
                test_board = board.copy()
                test_board.set_stone(move[0], move[1], color)
                captures = rules.check_captures(test_board, move[0], move[1], color)
                total = sum(len(g) for g in captures)
                scored.append((move, total))
            scored.sort(key=lambda x: x[1], reverse=True)
            # 75%概率选最好的，25%随机选前3
            if random.random() < 0.75:
                return scored[0][0]
            return random.choice(scored[:min(3, len(scored))])[0]

        # 防守 - 选择能增加最多气的走法
        defensive_moves = self.find_defensive_moves(board, color, rules, ko_point)
        if defensive_moves:
            scored = []
            for move in defensive_moves:
                test_board = board.copy()
                test_board.set_stone(move[0], move[1], color)
                new_group = test_board.get_group(move[0], move[1])
                libs = test_board.get_liberties(new_group)
                scored.append((move, libs))
            scored.sort(key=lambda x: x[1], reverse=True)
            return scored[0][0]

        # 开局走星位
        opening_moves = self.find_opening_moves(board)
        if opening_moves:
            return random.choice(opening_moves)

        # 选靠近棋子的位置，不走孤棋
        scored_moves = []
        for move in valid_moves:
            x, y = move
            neighbors = 0
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if board.is_valid_position(nx, ny) and not board.is_empty(nx, ny):
                        neighbors += 1
            scored_moves.append((move, neighbors))

        scored_moves.sort(key=lambda x: x[1], reverse=True)
        top = scored_moves[:max(5, len(scored_moves) // 3)]
        return random.choice(top)[0]
    
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
        self._eval_cache = {}
    
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
        
        if ko_point is not None:
            ko_threats = self.find_ko_threats(board, color, ko_point, rules)
            if ko_threats:
                best_threat = None
                best_score = -float('inf')
                
                for threat in ko_threats:
                    test_board = board.copy()
                    test_board.set_stone(threat[0], threat[1], color)
                    score = self.evaluate_position(test_board, color)
                    if score > best_score:
                        best_score = score
                        best_threat = threat
                
                if best_threat:
                    return best_threat
        
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
        self.untried_moves = None

    def get_untried_moves(self):
        if self.untried_moves is None:
            self.untried_moves = []
            for y in range(self.board.size):
                for x in range(self.board.size):
                    if self.rules.is_valid_move(self.board, x, y, self.color, self.ko_point):
                        self.untried_moves.append((x, y))
        return self.untried_moves

    def is_fully_expanded(self):
        return len(self.get_untried_moves()) == 0

    def is_terminal(self):
        if not self.get_untried_moves() and not self.children:
            return True
        for y in range(self.board.size):
            for x in range(self.board.size):
                if self.rules.is_valid_move(self.board, x, y, self.color, self.ko_point):
                    return False
        return True

    def place_with_captures(self, board, x, y, color, ko_point=None):
        """落子并处理吃子，返回新的劫点"""
        if not self.rules.is_valid_move(board, x, y, color, ko_point):
            return None
        board.set_stone(x, y, color)
        captures = self.rules.check_captures(board, x, y, color)
        for group in captures:
            for (cx, cy) in group:
                board.set_stone(cx, cy, None)
        # 检测是否形成劫
        if len(captures) == 1 and len(captures[0]) == 1:
            return captures[0]
        return None

    def simulate(self):
        sim_board = self.board.copy()
        sim_color = self.color
        sim_ko = self.ko_point
        rules = self.rules

        for _ in range(50):
            valid_moves = []
            for y in range(sim_board.size):
                for x in range(sim_board.size):
                    if rules.is_valid_move(sim_board, x, y, sim_color, sim_ko):
                        valid_moves.append((x, y))
            if not valid_moves:
                break
            # 启发式偏置：优先选吃子和连接
            if len(valid_moves) > 10:
                scored = []
                for mx, my in valid_moves:
                    score = 0
                    # 吃子奖励
                    test_b = sim_board.copy()
                    test_b.set_stone(mx, my, sim_color)
                    caps = rules.check_captures(test_b, mx, my, sim_color)
                    if caps:
                        score += sum(len(g) for g in caps) * 50
                    # 靠近棋子奖励
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nx, ny = mx + dx, my + dy
                        if sim_board.is_valid_position(nx, ny) and not sim_board.is_empty(nx, ny):
                            score += 5
                    scored.append(score)
                # 按分数偏置选择
                max_score = max(scored)
                if max_score > 0:
                    candidates = [v for v, s in zip(valid_moves, scored) if s >= max_score * 0.8]
                    move = random.choice(candidates)
                else:
                    move = random.choice(valid_moves)
            else:
                move = random.choice(valid_moves)
            new_ko = self.place_with_captures(sim_board, move[0], move[1], sim_color, sim_ko)
            if new_ko is not None:
                sim_ko = new_ko
            else:
                sim_ko = None
            sim_color = 'W' if sim_color == 'B' else 'B'

        return self._evaluate_sim(sim_board, self.color)

    def _evaluate_sim(self, board, color):
        """模拟评估：更真实的局面评分"""
        opponent = 'W' if color == 'B' else 'B'
        score = 0
        all_groups = board.get_all_groups()
        for group in all_groups:
            group_color = board.get_stone(group[0][0], group[0][1])
            group_size = len(group)
            liberties = board.get_liberties(group)
            multiplier = 1 if group_color == color else -1
            score += group_size * 3 * multiplier
            if liberties <= 1:
                score -= 20 * multiplier
        return score


class HardAI(AI):
    def __init__(self):
        self.mcts_iterations = 2000
        self.mcts_time_limit = 8.0
        self.start_time = 0
    
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
                
                if liberties >= 4:
                    score += 15
                elif liberties == 3:
                    score += 10
                elif liberties == 2:
                    score += 5
                elif liberties == 1:
                    score -= 30
            else:
                score -= group_size * 3
                
                if liberties >= 4:
                    score -= 15
                elif liberties == 3:
                    score -= 10
                elif liberties == 2:
                    score -= 5
                elif liberties == 1:
                    score += 30
        
        return score
    
    def mcts(self, board, color, rules, ko_point):
        root = MCTSNode(board.copy(), color, rules, ko_point)

        end_time = time.time() + self.mcts_time_limit

        for _ in range(self.mcts_iterations):
            if time.time() > end_time:
                break

            node = root
            sim_board = node.board.copy()
            sim_color = node.color
            sim_ko = node.ko_point
            sim_node_ko = sim_ko

            # Selection: 遍历已展开节点
            while node.children:
                node = max(node.children, key=lambda n: (n.wins / (n.visits + 1)) + math.sqrt(2 * math.log(node.visits + 1) / (n.visits + 1)))
                # 模拟执行该步落子（含吃子），传递当前劫点
                sim_node_ko = node.place_with_captures(sim_board, node.move[0], node.move[1], sim_color, sim_ko)
                sim_ko = sim_node_ko
                sim_color = 'W' if sim_color == 'B' else 'B'

            # Expansion: 展开一个未尝试的走法
            if node.get_untried_moves():
                move = node.get_untried_moves().pop(random.randint(0, len(node.get_untried_moves()) - 1))
                new_node = MCTSNode(sim_board.copy(), sim_color, rules, sim_node_ko, parent=node, move=move)
                node.children.append(new_node)
                node = new_node
                sim_node_ko = node.place_with_captures(sim_board, move[0], move[1], sim_color, sim_ko)
                sim_ko = sim_node_ko
                sim_color = 'W' if sim_color == 'B' else 'B'

            # Simulation: 随机模拟到终局
            result = node.simulate()
            node.wins += result
            node.visits += 1

            # Backpropagation: 将结果传播到所有祖先节点
            while node.parent:
                node = node.parent
                node.wins += result
                node.visits += 1

        if not root.children:
            return None

        best_child = max(root.children, key=lambda n: n.visits)
        return best_child.move
    
    def _get_opening_move(self, board, color):
        """开局阶段选择星位或常见定式位置"""
        if board.size >= 9:
            openings = [(3, 3), (3, 9), (3, 15), (9, 3), (9, 9), (9, 15), (15, 3), (15, 9), (15, 15)]
            if board.size == 9:
                openings = [(2, 2), (2, 6), (4, 4), (6, 2), (6, 6)]
            elif board.size == 13:
                openings = [(3, 3), (3, 6), (3, 9), (6, 3), (6, 6), (6, 9), (9, 3), (9, 6), (9, 9)]
            # 检查棋盘上总棋子数是否小于等于2
            total = sum(1 for y in range(board.size) for x in range(board.size) if not board.is_empty(x, y))
            if total <= 1:
                for ox, oy in openings:
                    if board.is_empty(ox, oy):
                        return (ox, oy)
        return None

    def get_move(self, board, color, rules, ko_point=None) -> Optional[Tuple[int, int]]:
        if ko_point is not None:
            ko_threats = self.find_ko_threats(board, color, ko_point, rules)
            if ko_threats:
                best_threat = None
                best_score = -float('inf')
                for threat in ko_threats:
                    test_board = board.copy()
                    test_board.set_stone(threat[0], threat[1], color)
                    score = self.evaluate_position(test_board, color)
                    if score > best_score:
                        best_score = score
                        best_threat = threat
                if best_threat:
                    return best_threat

        # 开局走星位
        opening = self._get_opening_move(board, color)
        if opening:
            return opening

        all_valid = []
        for y in range(board.size):
            for x in range(board.size):
                if rules.is_valid_move(board, x, y, color, ko_point):
                    all_valid.append((x, y))
        if not all_valid:
            return None

        # 吃子优先
        for x, y in all_valid:
            test_board = board.copy()
            test_board.set_stone(x, y, color)
            captures = rules.check_captures(test_board, x, y, color)
            if captures:
                total_captured = sum(len(g) for g in captures)
                if total_captured >= 2:
                    return (x, y)

        move = self.mcts(board, color, rules, ko_point)
        if move:
            return move

        return random.choice(all_valid)
    
    def get_best_moves_with_scores(self, board, color, rules, ko_point=None):
        valid_moves = []
        for y in range(board.size):
            for x in range(board.size):
                if rules.is_valid_move(board, x, y, color, ko_point):
                    valid_moves.append((x, y))
        
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
