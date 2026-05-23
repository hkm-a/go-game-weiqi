"""围棋基础规则测试套件"""
import pytest
from game.board import Board
from game.rules import Rules


class TestBasicCaptures:
    """测试基本吃子功能"""

    def test_capture_one_stone(self):
        """测试吃掉一个子"""
        board = Board(9)
        rules = Rules()
        board.set_stone(4, 3, 'B')
        board.set_stone(3, 4, 'B')
        board.set_stone(5, 4, 'B')
        board.set_stone(4, 4, 'W')

        success, captured, ko = rules.place_stone(board, 4, 5, 'B')
        assert success, "应该能吃掉1个子"
        assert captured == 1, f"应该吃1个子，实际{captured}个"


class TestSuicideRule:
    """测试自杀禁止规则"""

    def test_suicide_forbidden(self):
        """测试自杀被禁止"""
        board = Board(9)
        rules = Rules()
        board.set_stone(4, 4, 'B')
        board.set_stone(3, 4, 'W')
        board.set_stone(5, 4, 'W')
        board.set_stone(4, 3, 'W')
        board.set_stone(4, 5, 'W')

        success, captured, ko = rules.place_stone(board, 4, 4, 'B')
        assert not success, "自杀应该被禁止"

    def test_capture_allowed_if_not_suicide(self):
        """测试非自杀的吃子应该被允许"""
        board = Board(9)
        rules = Rules()
        board.set_stone(4, 4, 'W')
        board.set_stone(3, 4, 'B')
        board.set_stone(5, 4, 'B')
        board.set_stone(4, 3, 'B')

        success, captured, ko = rules.place_stone(board, 4, 5, 'B')
        assert success, "应该能吃子（不是自杀）"
        assert captured == 1, "应该吃1个子"


class TestKoRule:
    """测试打劫规则"""

    def test_ko_detection_place_stone_works(self):
        """验证落子函数正常工作"""
        board = Board(9)
        rules = Rules()
        # 在空位落子
        success, captured, ko = rules.place_stone(board, 4, 4, 'B')
        assert success, "应在空位成功落子"
        assert captured == 0, "不应吃子"

    def test_ko_point_blocks_immediate_recapture(self):
        """验证劫点阻止立即回提"""
        board = Board(9)
        rules = Rules()
        # 构造劫形
        board.set_stone(4, 3, 'B')
        board.set_stone(3, 4, 'B')
        board.set_stone(5, 4, 'B')
        board.set_stone(4, 5, 'W')
        board.set_stone(3, 5, 'W')
        board.set_stone(5, 5, 'W')

        # W 在 (4,4) 提 B 在 (4,4) 的一子 → 形成劫
        success1, captured1, ko1 = rules.place_stone(board, 4, 4, 'W')
        assert success1, "白棋应能提子"

        # B 试图立即回提 — ko_point 应阻止
        success2, captured2, ko2 = rules.place_stone(board, 4, 4, 'B', ko1)
        assert not success2, "劫点应阻止立即回提"


class TestForbiddenPoints:
    """测试禁着点（待扩展）"""
    pass
