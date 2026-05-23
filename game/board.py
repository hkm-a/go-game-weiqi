class Board:
    def __init__(self, size=19):
        self.size = size
        self.board = [[None for _ in range(size)] for _ in range(size)]
    
    def is_valid_position(self, x, y):
        return 0 <= x < self.size and 0 <= y < self.size
    
    def get_stone(self, x, y):
        if not self.is_valid_position(x, y):
            return None
        return self.board[y][x]
    
    def set_stone(self, x, y, color):
        if not self.is_valid_position(x, y):
            return False
        if color not in ['B', 'W', None]:
            return False
        self.board[y][x] = color
        return True
    
    def is_empty(self, x, y):
        if not self.is_valid_position(x, y):
            return False
        return self.board[y][x] is None
    
    def copy(self):
        new_board = Board(self.size)
        for y in range(self.size):
            for x in range(self.size):
                new_board.board[y][x] = self.board[y][x]
        return new_board
    
    def get_group(self, x, y):
        if not self.is_valid_position(x, y) or self.board[y][x] is None:
            return []
        
        color = self.board[y][x]
        group = []
        visited = set()
        stack = [(x, y)]
        
        while stack:
            cx, cy = stack.pop()
            if (cx, cy) in visited:
                continue
            if not self.is_valid_position(cx, cy):
                continue
            if self.board[cy][cx] != color:
                continue
            
            visited.add((cx, cy))
            group.append((cx, cy))
            
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                stack.append((cx + dx, cy + dy))
        
        return group
    
    def get_liberties(self, group):
        liberties = set()
        for (x, y) in group:
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if self.is_valid_position(nx, ny) and self.is_empty(nx, ny):
                    liberties.add((nx, ny))
        return len(liberties)
    
    def get_all_groups(self):
        groups = []
        visited = set()
        
        for y in range(self.size):
            for x in range(self.size):
                if (x, y) in visited:
                    continue
                if self.board[y][x] is None:
                    continue
                
                group = self.get_group(x, y)
                for pos in group:
                    visited.add(pos)
                groups.append(group)
        
        return groups
    
    def get_state_hash(self):
        state = []
        for y in range(self.size):
            row = []
            for x in range(self.size):
                stone = self.board[y][x]
                if stone == 'B':
                    row.append('1')
                elif stone == 'W':
                    row.append('2')
                else:
                    row.append('0')
            state.append(''.join(row))
        return '|'.join(state)
