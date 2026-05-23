from board import Board
from rules import Rules

def debug_self_capture():
    board = Board(9)
    rules = Rules()
    
    board.set_stone(3, 4, 'B')
    board.set_stone(5, 4, 'B')
    board.set_stone(4, 3, 'B')
    
    print("Initial board:")
    for y in range(9):
        row = []
        for x in range(9):
            s = board.get_stone(x, y)
            row.append(s if s else '.')
        print(''.join(row))
    
    test_board = board.copy()
    test_board.set_stone(4, 4, 'W')
    
    print("\nAfter placing W at (4,4):")
    for y in range(9):
        row = []
        for x in range(9):
            s = test_board.get_stone(x, y)
            row.append(s if s else '.')
        print(''.join(row))
    
    captures = rules.check_captures(test_board, 4, 4, 'W')
    print("\nCaptures:", captures)
    
    group = test_board.get_group(4, 4)
    print("Group:", group)
    print("Liberties:", test_board.get_liberties(group))
    
    would_capture = rules.would_self_capture(board, 4, 4, 'W')
    print("\nwould_self_capture:", would_capture)
    
    success, captured, ko = rules.place_stone(board, 4, 4, 'W')
    print("\nplace_stone result: success=", success, "captured=", captured, "ko=", ko)

if __name__ == "__main__":
    debug_self_capture()
