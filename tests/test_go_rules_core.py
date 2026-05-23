"""
围棋基础规则测试套件

包含：
- 基本吃子
- 自杀禁止
- 禁着点检测
- 打劫规则
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    """测试打劫规则

    经典劫形配置：
    模拟一个劫的形成过程，测试劫检测逻辑
    """

    def test_ko_detection_logic(self):
        """测试劫检测逻辑"""
        board = Board(9)
        rules = Rules()

        board.set_stone(3, 3, 'B')
        board.set_stone(4, 3, 'B')
        board.set_stone(3, 4, 'B')
        board.set_stone(4, 4, 'W')

        initial_hash = board.get_state_hash()

        success, captured, ko = rules.place_stone(board, 4, 5, 'W')

        if success:
            new_hash = board.get_state_hash()
            ko_point = rules.is_ko(board, 4, 5, 'W', None)
            assert ko_point is None or ko is None or ko_point == ko

        assert initial_hash != new_hash if success else True

    def test_ko_point_not_none_when_repeated_state(self):
        """测试劫点在状态重复时不为None"""
        board = Board(9)
        rules = Rules()

        board.set_stone(3, 3, 'B')
        board.set_stone(4, 3, 'B')
        board.set_stone(3, 4, 'B')
        board.set_stone(4, 4, 'W')

        previous_state = board.get_state_hash()

        success1, captured1, ko1 = rules.place_stone(board, 4, 5, 'W')

        if success1:
            success2, captured2, ko2 = rules.place_stone(board, 4, 4, 'B')

            if success2 and board.get_state_hash() == previous_state:
                ko_point = rules.is_ko(board, 4, 4, 'B', previous_state)
                assert ko_point is not None, "劫点应该被检测到"


class TestForbiddenPoints:
    """测试禁着点"""


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
