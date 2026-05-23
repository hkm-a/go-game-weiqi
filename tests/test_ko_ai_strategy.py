"""AI劫材策略测试套件"""
import pytest
from game.board import Board
from game.rules import Rules
from game.ai import EasyAI, MediumAI


@pytest.fixture
def ko_board():
    """构造一个含劫的棋盘"""
    board = Board(9)
    board.set_stone(3, 1, 'B')
    board.set_stone(2, 2, 'B')
    board.set_stone(4, 2, 'B')
    board.set_stone(3, 3, 'B')
    board.set_stone(3, 2, 'W')
    return board


class TestKoThreatDetection:
    """测试劫材检测"""

    def test_find_ko_threats_returns_list(self, ko_board):
        """验证劫材搜索返回列表"""
        rules = Rules()
        ai = EasyAI()

        ko_threats = ai.find_ko_threats(ko_board, 'B', (2, 2), rules)
        assert isinstance(ko_threats, list), "应该返回劫材列表"


class TestEasyAIWithKo:
    """测试EasyAI劫材策略"""

    def test_easy_ai_finds_ko_threat(self, ko_board):
        """验证EasyAI在劫存在时找到劫材"""
        rules = Rules()
        ai = EasyAI()

        move = ai.get_move(ko_board, 'B', rules, (2, 2))
        assert move is not None, "AI应该返回劫材位置"
        assert move != (2, 2), "劫材不应该是劫点本身"


class TestMediumAIWithKo:
    """测试MediumAI劫材策略"""

    def test_medium_ai_finds_ko_threat(self, ko_board):
        """验证MediumAI在劫存在时找到劫材"""
        rules = Rules()
        ai = MediumAI()

        move = ai.get_move(ko_board, 'B', rules, (2, 2))
        assert move is not None, "AI应该返回劫材位置"
        assert move != (2, 2), "劫材不应该是劫点本身"


class TestAINoKo:
    """测试AI在无劫时行为"""

    def test_ai_plays_normally_without_ko(self):
        """验证AI在无劫时正常落子"""
        board = Board(9)
        rules = Rules()
        ai = EasyAI()
        board.set_stone(3, 3, 'B')
        board.set_stone(3, 4, 'B')

        move = ai.get_move(board, 'B', rules, None)
        assert move is not None, "AI应该返回落子位置"
