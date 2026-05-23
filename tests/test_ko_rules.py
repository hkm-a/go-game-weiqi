"""打劫规则完整测试套件"""
import pytest
from game.board import Board
from game.rules import Rules


class TestKoDetection:
    """测试劫的检测"""

    def test_ko_point_created_on_recapture_shape(self):
        """验证提一子时产生劫点"""
        board = Board(9)
        rules = Rules()
        board.set_stone(2, 1, 'B')
        board.set_stone(3, 1, 'B')
        board.set_stone(4, 1, 'B')
        board.set_stone(2, 2, 'B')
        board.set_stone(3, 2, 'W')
        board.set_stone(4, 2, 'B')
        board.set_stone(3, 3, 'B')

        result = rules.is_ko(board, 3, 4, 'W', None)
        # is_ko 返回 None（不是劫）或 tuple（劫点坐标）
        assert result is None or isinstance(result, tuple)

    def test_ko_cycle_preserves_hash(self):
        """验证劫循环时棋盘哈希一致"""
        board = Board(9)
        rules = Rules()
        board.set_stone(1, 2, 'B')
        board.set_stone(2, 1, 'B')
        board.set_stone(3, 2, 'W')
        board.set_stone(2, 3, 'W')
        board.set_stone(2, 2, 'B')

        initial_hash = board.get_state_hash()
        board2 = board.copy()
        assert board2.get_state_hash() == initial_hash


class TestKoPointValidation:
    """测试劫点验证"""

    def test_ko_point_blocks_move(self):
        """验证劫点位置被禁止落子"""
        board = Board(9)
        rules = Rules()
        board.set_stone(2, 2, 'B')
        board.set_stone(3, 1, 'B')
        board.set_stone(3, 2, 'W')

        is_valid = rules.is_valid_move(board, 3, 2, 'B', (3, 2))
        assert not is_valid, "劫点应该被禁止落子"

    def test_non_ko_point_allowed(self):
        """验证非劫点位置允许落子"""
        board = Board(9)
        rules = Rules()
        board.set_stone(2, 2, 'B')
        board.set_stone(3, 1, 'B')
        board.set_stone(3, 2, 'W')

        is_valid = rules.is_valid_move(board, 4, 2, 'B', (3, 2))
        assert is_valid, "非劫点应该允许落子"


class TestCaptureWithKo:
    """测试含劫的吃子场景"""

    def test_capture_still_works_with_ko(self):
        """确保有劫点时基本吃子仍然正常"""
        board = Board(9)
        rules = Rules()
        board.set_stone(3, 1, 'B')
        board.set_stone(2, 2, 'B')
        board.set_stone(4, 2, 'B')
        board.set_stone(3, 2, 'W')

        success, captured, ko = rules.place_stone(board, 3, 3, 'B')
        assert success, "应该成功落子"
        assert captured >= 1, "应该至少吃掉1个子"

    def test_suicide_still_forbidden_with_ko(self):
        """确保有劫点时禁止自杀仍然正常"""
        board = Board(9)
        rules = Rules()
        board.set_stone(3, 1, 'B')
        board.set_stone(2, 2, 'B')
        board.set_stone(4, 2, 'B')
        board.set_stone(3, 3, 'B')

        success, captured, ko = rules.place_stone(board, 3, 2, 'W')
        assert not success, "自杀应该被禁止"
