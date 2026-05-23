from board import Board
from rules import Rules

def test_basic_move():
    board = Board(9)
    rules = Rules()
    success, captured, ko = rules.place_stone(board, 4, 4, 'B')
    assert success
    assert captured == 0
    assert ko is None
    assert board.get_stone(4, 4) == 'B'
    print("test_basic_move passed")

def test_capture():
    board = Board(9)
    rules = Rules()
    board.set_stone(3, 4, 'W')
    board.set_stone(5, 4, 'W')
    board.set_stone(4, 3, 'W')
    board.set_stone(4, 4, 'B')
    
    success, captured, ko = rules.place_stone(board, 4, 5, 'W')
    assert success
    assert captured == 1
    assert board.get_stone(4, 4) is None
    print("test_capture passed")

def test_ko():
    board = Board(9)
    rules = Rules()
    
    board.set_stone(2, 3, 'B')
    board.set_stone(4, 3, 'B')
    board.set_stone(3, 2, 'B')
    board.set_stone(3, 4, 'W')
    board.set_stone(2, 4, 'W')
    board.set_stone(4, 4, 'W')
    
    success, captured, ko = rules.place_stone(board, 3, 3, 'W')
    assert success
    assert captured == 0
    
    success, captured, ko = rules.place_stone(board, 3, 5, 'B')
    assert success
    assert captured == 1
    assert ko is not None
    
    success, captured, new_ko = rules.place_stone(board, ko[0], ko[1], 'W', ko)
    assert not success
    print("test_ko passed")

def test_self_capture():
    board = Board(9)
    rules = Rules()
    
    board.set_stone(3, 4, 'B')
    board.set_stone(5, 4, 'B')
    board.set_stone(4, 3, 'B')
    board.set_stone(4, 5, 'B')
    
    success, captured, ko = rules.place_stone(board, 4, 4, 'W')
    assert not success
    print("test_self_capture passed")

def test_self_capture_with_capture():
    board = Board(9)
    rules = Rules()
    
    board.set_stone(3, 4, 'B')
    board.set_stone(5, 4, 'B')
    board.set_stone(4, 3, 'B')
    board.set_stone(4, 5, 'W')
    
    success, captured, ko = rules.place_stone(board, 4, 4, 'W')
    assert success
    assert captured == 0
    print("test_self_capture_with_capture passed")

if __name__ == "__main__":
    test_basic_move()
    test_capture()
    test_self_capture()
    test_self_capture_with_capture()
    print("Basic tests passed!")
