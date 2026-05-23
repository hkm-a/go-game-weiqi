"""胜负判定与终局测试套件"""
import pytest
from game.board import Board
from game.rules import Rules
from game.game_state import GameState


def make_territory_board(size, positions, color):
    """在指定位置放置棋子，返回 Board 实例"""
    board = Board(size)
    for x, y in positions:
        board.set_stone(x, y, color)
    return board


class TestTerritoryCalculation:
    """测试领地计算功能"""

    def test_empty_territory_black(self):
        """测试黑棋获得领地"""
        board = make_territory_board(9, [(0, 0), (1, 0), (0, 1)], 'B')
        game_state = GameState()
        game_state.board = board

        black_terr, white_terr = game_state.calculate_territory()
        # 简单的洪水算法会把所有连通空格算为领地
        assert black_terr > 0, f"黑方应有领地，实际{black_terr}"
        assert white_terr == 0, "白方应无领地"

    def test_white_territory_in_corner(self):
        """测试白棋获得领地"""
        board = make_territory_board(9, [(8, 8), (7, 8), (8, 7)], 'W')
        game_state = GameState()
        game_state.board = board

        black_terr, white_terr = game_state.calculate_territory()
        assert white_terr > 0, f"白方应有领地，实际{white_terr}"
        assert black_terr == 0, "黑方应无领地"

    def test_disconnected_stones_no_extra_territory(self):
        """孤立棋子不产生额外领地"""
        board = make_territory_board(9, [(0, 0), (1, 0), (0, 1)], 'B')
        board.set_stone(4, 4, 'B')  # 孤子

        game_state = GameState()
        game_state.board = board

        black_terr, white_terr = game_state.calculate_territory()
        # 孤子 (4,4) 不产生领地
        assert white_terr == 0, "白方应无领地"
        assert black_terr + white_terr < 81, "领地不应超过棋盘总数"


class TestScoreCalculation:
    """测试分数计算功能"""

    def test_basic_score_has_required_fields(self):
        """验证终局分数包含所有必需字段"""
        board = make_territory_board(9, [(4, 4), (0, 0), (0, 1)], 'B')
        board.set_stone(8, 8, 'W')
        board.set_stone(8, 7, 'W')
        board.set_stone(7, 8, 'W')

        game_state = GameState()
        game_state.board = board
        game_state.end_game()

        assert game_state.final_score is not None, "应有最终分数"
        assert set(game_state.final_score.keys()) >= {
            'black', 'white', 'black_territory', 'white_territory',
            'black_stones', 'white_stones'
        }, "分数应包含所有必需字段"

    def test_black_stones_count(self):
        """测试黑子计数"""
        board = make_territory_board(9, [(0, 0), (1, 1), (2, 2)], 'B')
        game_state = GameState()
        game_state.board = board
        game_state.end_game()

        assert game_state.final_score['black_stones'] == 3, "应有3个黑子"

    def test_white_stones_count(self):
        """测试白子计数"""
        board = make_territory_board(9, [(8, 8), (7, 7)], 'W')
        game_state = GameState()
        game_state.board = board
        game_state.end_game()

        assert game_state.final_score['white_stones'] == 2, "应有2个白子"

    def test_komi_white_wins_with_equal_stones(self):
        """测试贴目使白方在子数相等时获胜"""
        board = make_territory_board(9, [(0, 0), (1, 0), (0, 1)], 'B')
        board.set_stone(8, 8, 'W')

        game_state = GameState()
        game_state.board = board
        game_state.end_game()

        assert game_state.final_score['white'] > game_state.final_score['black'], \
            "白方因贴目3.75子，应分数更高"


class TestGameEndDetection:
    """测试终局检测功能"""

    def test_consecutive_passes_end_game(self):
        """测试连续两次PASS进入死子标记模式"""
        game_state = GameState()

        game_state.pass_move()
        assert game_state.consecutive_passes == 1
        assert game_state.game_status == 'playing'

        game_state.pass_move()
        assert game_state.consecutive_passes == 2
        assert game_state.game_status == 'end_marking', "两次PASS后应进入死子标记模式"

    def test_move_after_pass_resets_counter(self):
        """测试落子重置连续PASS计数"""
        game_state = GameState()

        game_state.pass_move()
        assert game_state.consecutive_passes == 1

        # 在空棋盘中心落子
        game_state.make_move(9, 9)
        assert game_state.consecutive_passes == 0, "落子后PASS计数应重置"


class TestInfluenceMap:
    """测试势力图计算"""

    def test_influence_stronger_near_stone(self):
        """测试棋子附近影响力更强"""
        board = Board(9)
        board.set_stone(4, 4, 'B')
        board.set_stone(6, 6, 'W')

        game_state = GameState()
        game_state.board = board

        influence = game_state.calculate_influence_map()

        assert len(influence) == 9, "势力图应为9x9"
        assert len(influence[0]) == 9, "势力图应为9x9"

        # (4,4) 的黑子对 (4,4) 本身影响力最大
        assert influence[4][4] > influence[0][0], \
            "中心点受黑子影响应大于角落"
