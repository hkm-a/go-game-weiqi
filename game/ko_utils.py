from game.board import Board
from game.rules import Rules

class KoUtils:
    """打劫相关工具类"""
    
    @staticmethod
    def find_ko_threats(board, color, max_results=10):
        """
        寻找劫材位置
        
        Args:
            board: 当前棋盘
            color: 需要找劫材的颜色 ('B' or 'W')
            max_results: 返回的最大结果数
        
        Returns:
            劫材位置列表 [(x, y), ...]，按威胁程度排序
        """
        threats = []
        rules = Rules()
        
        for y in range(board.size):
            for x in range(board.size):
                if not board.is_empty(x, y):
                    continue
                
                if not rules.is_valid_move(board, x, y, color, None):
                    continue
                
                # 评估这个位置作为劫材的威胁程度
                threat_score = KoUtils._evaluate_ko_threat(board, x, y, color)
                if threat_score > 0:
                    threats.append((x, y, threat_score))
        
        # 按威胁程度降序排序
        threats.sort(key=lambda item: item[2], reverse=True)
        
        # 返回前max_results个结果
        return [(t[0], t[1]) for t in threats[:max_results]]
    
    @staticmethod
    def _evaluate_ko_threat(board, x, y, color):
        """
        评估一个位置作为劫材的威胁程度
        
        Returns:
            威胁分数，0-100
        """
        score = 0
        enemy = 'W' if color == 'B' else 'B'
        
        # 1. 靠近敌方棋子（+20分/每个）
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if board.is_valid_position(nx, ny) and board.get_stone(nx, ny) == enemy:
                score += 20
        
        # 2. 在角上（+15分）
        if (x < 3 or x >= board.size - 3) and (y < 3 or y >= board.size - 3):
            score += 15
        
        # 3. 在边上（+10分）
        if x < 3 or x >= board.size - 3 or y < 3 or y >= board.size - 3:
            score += 10
        
        # 4. 有空间可以扩展（+5分/每个）
        space = 0
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            nx, ny = x + dx, y + dy
            if board.is_valid_position(nx, ny) and board.is_empty(nx, ny):
                space += 1
        score += space * 5
        
        # 5. 检测是否能吃掉附近的棋子
        if KoUtils._can_capture_nearby(board, x, y, color):
            score += 30
        
        return min(score, 100)
    
    @staticmethod
    def _can_capture_nearby(board, x, y, color):
        """
        检查在位置 x, y 落子后是否能吃掉附近的敌方棋子
        """
        enemy = 'W' if color == 'B' else 'B'
        rules = Rules()
        
        test_board = board.copy()
        success, captured, _ = rules.place_stone(test_board, x, y, color)
        
        return success and captured > 0
