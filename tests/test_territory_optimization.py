"""领地计算优化测试套件"""
import pytest
import time
from game.board import Board
from game.game_state import GameState


class TestContestedTerritory:
    """测试争议区域处理"""

    def test_contested_area_not_counted(self):
        """验证争议区域不计入任何一方"""
        state = GameState()
        state.board.set_stone(0, 0, 'B')
        state.board.set_stone(2, 0, 'W')

        black_terr, white_terr = state.calculate_territory()
        # (1,0) 同时接触黑白双方，是争议区域
        assert black_terr == 0
        assert white_terr == 0

    def test_neutral_area_not_counted(self):
        """验证完全无接触的中立区域不计分"""
        state = GameState()

        black_terr, white_terr = state.calculate_territory()
        assert black_terr == 0
        assert white_terr == 0

    def test_corner_territory_returns_int(self):
        """验证角部领地计算返回整数"""
        state = GameState()
        state.board.set_stone(0, 0, 'B')
        state.board.set_stone(0, 3, 'W')

        black_terr, white_terr = state.calculate_territory()
        assert isinstance(black_terr, int)
        assert isinstance(white_terr, int)

    def test_edge_territory_returns_int(self):
        """验证边部领地计算返回整数"""
        state = GameState()
        state.board.set_stone(0, 0, 'B')
        state.board.set_stone(0, 3, 'W')

        black_terr, white_terr = state.calculate_territory()
        assert isinstance(black_terr, int)
        assert isinstance(white_terr, int)


class TestLargeBoard:
    """测试大棋盘性能"""

    def test_large_board_efficiency(self):
        """验证大棋盘计算在合理时间内完成"""
        state = GameState()

        for y in range(0, 5):
            for x in range(0, 5):
                state.board.set_stone(x, y, 'B')
        for y in range(14, 19):
            for x in range(14, 19):
                state.board.set_stone(x, y, 'W')

        start_time = time.time()
        state.calculate_territory()
        elapsed = time.time() - start_time

        assert elapsed < 1.0, f"领地计算超时：{elapsed:.2f}s"
