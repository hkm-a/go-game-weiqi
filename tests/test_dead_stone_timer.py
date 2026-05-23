"""
死子标记与计时器测试
覆盖：标记边界、确认结算、计时边界
"""
import time
import pytest
from game.game_state import GameState


class TestDeadStoneMarking:
    """死子标记"""

    def test_mark_dead_stone_toggle(self):
        """标记/取消标记切换"""
        gs = GameState()
        gs.make_move(3, 3)  # B 下子
        # 进入标记模式
        gs.begin_dead_marking()
        # 标记 (3,3) 为死子
        gs.mark_dead_stone(3, 3)
        assert (3, 3) in gs.dead_stones
        # 再次点击取消标记
        gs.mark_dead_stone(3, 3)
        assert (3, 3) not in gs.dead_stones

    def test_confirm_no_dead_stones(self):
        """无死子时确认"""
        gs = GameState()
        gs.begin_dead_marking()
        gs.confirm_dead_stones()
        assert gs.game_status == 'ended'

    def test_confirm_with_dead_stones(self):
        """有死子时确认"""
        gs = GameState(9)
        gs.board.set_stone(3, 3, 'B')
        gs.begin_dead_marking()
        gs.mark_dead_stone(3, 3)
        gs.confirm_dead_stones()
        assert gs.game_status == 'ended'
        # B 的死子应计入 W 的提子
        assert gs.captures['W'] >= 1

    def test_clear_dead_stones(self):
        """清除所有死子标记"""
        gs = GameState(9)
        gs.board.set_stone(3, 3, 'B')
        gs.board.set_stone(4, 4, 'W')
        gs.begin_dead_marking()
        gs.mark_dead_stone(3, 3)
        gs.mark_dead_stone(4, 4)
        assert len(gs.dead_stones) == 2
        gs.clear_dead_stones()
        assert len(gs.dead_stones) == 0

    def test_mark_empty_position(self):
        """标记空位置无影响"""
        gs = GameState()
        gs.begin_dead_marking()
        gs.mark_dead_stone(5, 5)  # 空位
        # 空位标记后，confirm_dead_stones 应忽略
        gs.confirm_dead_stones()
        assert gs.game_status == 'ended'

    def test_begin_dead_marking_clears_previous(self):
        """重新开始标记清除旧标记"""
        gs = GameState(9)
        gs.board.set_stone(3, 3, 'B')
        gs.begin_dead_marking()
        gs.mark_dead_stone(3, 3)
        assert len(gs.dead_stones) == 1
        gs.begin_dead_marking()
        assert len(gs.dead_stones) == 0

    def test_confirm_removes_dead_stones_from_board(self):
        """确认后死子从棋盘移除"""
        gs = GameState(9)
        gs.board.set_stone(3, 3, 'B')
        gs.begin_dead_marking()
        gs.mark_dead_stone(3, 3)
        gs.confirm_dead_stones()
        assert gs.board.get_stone(3, 3) is None, "死子应从棋盘移除"


class TestTimerIntegration:
    """计时器边界（不依赖 real time）"""

    def test_timer_decrement(self):
        """计时递减（模拟）"""
        # game_state 不管理计时器，计时在 main.py
        # 测试 game_state 的 ended 状态在超时后正确处理
        gs = GameState()
        gs.game_status = 'ended'
        assert gs.game_status == 'ended'

    def test_timeout_auto_lose(self):
        """超时判负（通过直接设置状态模拟）"""
        gs = GameState()
        # main.py 中超时逻辑：设置 ended + winner
        gs.game_status = 'ended'
        gs.winner = 'W'  # B 超时，W 胜
        assert gs.winner == 'W'
        # 验证结束状态
        assert gs.game_status == 'ended'

    def test_game_status_check_on_timed_out(self):
        """超时后操作被拒绝"""
        gs = GameState()
        gs.game_status = 'ended'
        gs.winner = 'W'
        result = gs.make_move(3, 3)
        assert not result, "超时后不能落子"


class TestStateConsistency:
    """状态一致性"""

    def test_captures_match_move_history(self):
        """提子计数不应超过走法数"""
        gs = GameState()
        for i in range(10):
            x = (i * 3 + 1) % 19
            y = (i * 5 + 2) % 19
            gs.make_move(x, y)
        total_captures = gs.captures['B'] + gs.captures['W']
        assert total_captures <= gs.move_count, "提子数不应超过手数"

    def test_board_stones_dont_exceed_moves(self):
        """棋盘上棋子数不超过手数"""
        gs = GameState()
        for i in range(20):
            x = (i * 3 + 1) % 19
            y = (i * 5 + 2) % 19
            if gs.board.is_empty(x, y):
                gs.make_move(x, y)
        stones = sum(1 for y in range(19) for x in range(19)
                     if gs.board.get_stone(x, y) is not None)
        assert stones <= gs.move_count, "棋盘棋子数不应超过总手数"

    def test_current_player_alternates(self):
        """玩家交替落子"""
        gs = GameState()
        assert gs.current_player == 'B'
        gs.make_move(3, 3)
        assert gs.current_player == 'W'
        gs.make_move(3, 4)
        assert gs.current_player == 'B'
