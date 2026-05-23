class Rules:
    def is_valid_move(self, board, x, y, color, ko_point=None):
        if not board.is_valid_position(x, y):
            return False
        if not board.is_empty(x, y):
            return False
        if ko_point is not None and (x, y) == ko_point:
            return False
        if self.would_self_capture(board, x, y, color):
            return False
        return True
    
    def remove_group(self, board, group):
        for (x, y) in group:
            board.set_stone(x, y, None)
    
    def check_captures(self, board, x, y, color):
        opponent = 'W' if color == 'B' else 'B'
        captured_groups = []
        
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if not board.is_valid_position(nx, ny):
                continue
            if board.get_stone(nx, ny) != opponent:
                continue
            
            group = board.get_group(nx, ny)
            if board.get_liberties(group) == 0:
                captured_groups.append(group)
        
        return captured_groups
    
    def would_self_capture(self, board, x, y, color):
        test_board = board.copy()
        test_board.set_stone(x, y, color)
        
        captures = self.check_captures(test_board, x, y, color)
        for group in captures:
            for pos in group:
                test_board.set_stone(pos[0], pos[1], None)
        
        group = test_board.get_group(x, y)
        return test_board.get_liberties(group) == 0
    
    def is_ko(self, board, x, y, color, previous_board):
        if previous_board is None:
            return None
        
        test_board = board.copy()
        test_board.set_stone(x, y, color)
        captures = self.check_captures(test_board, x, y, color)
        
        if len(captures) == 1 and len(captures[0]) == 1:
            captured = captures[0][0]
            temp_board = test_board.copy()
            self.remove_group(temp_board, captures[0])
            
            if temp_board.get_state_hash() == previous_board.get_state_hash():
                return captured
        
        return None
    
    def place_stone(self, board, x, y, color, ko_point=None):
        if not self.is_valid_move(board, x, y, color, ko_point):
            return (False, 0, None)
        
        board.set_stone(x, y, color)
        captures = self.check_captures(board, x, y, color)
        
        captured_count = 0
        new_ko_point = None
        
        for group in captures:
            captured_count += len(group)
            self.remove_group(board, group)
        
        if len(captures) == 1 and len(captures[0]) == 1:
            captured = captures[0][0]
            test_board = board.copy()
            test_board.set_stone(captured[0], captured[1], 'W' if color == 'B' else 'B')
            test_captures = self.check_captures(test_board, captured[0], captured[1], 'W' if color == 'B' else 'B')
            if len(test_captures) == 1 and len(test_captures[0]) == 1 and (x, y) in test_captures[0]:
                new_ko_point = captured
        
        return (True, captured_count, new_ko_point)
