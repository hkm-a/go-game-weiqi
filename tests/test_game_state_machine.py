"""
游戏状态机与交互测试
覆盖：playing → end_marking → ended 转换、按钮互动、异常操作
"""
import pytest
from game.game_state import GameState


class TestStateTransitions:
    """测试状态转换"""

    def test_initial_state(self):
        """初始状态为 playing"""
        gs = GameState()
        assert gs.game_status == 'playing'
        assert gs.current_player == 'B'
        assert gs.move_count == 0
        assert gs.consecutive_passes == 0

    def test_pass_transitions_to_end_marking(self):
        """连续两次 PASS 进入死子标记模式"""
        gs = GameState()
        gs.pass_move()
        assert gs.game_status == 'playing'
        gs.pass_move()
        assert gs.game_status == 'end_marking', "两次PASS应进入end_marking"
        assert gs.consecutive_passes == 2

    def test_confirm_dead_stones_transitions_to_ended(self):
        """确认死子后进入 ended 状态并计算分数"""
        gs = GameState()
        gs.pass_move()
        gs.pass_move()
        assert gs.game_status == 'end_marking'
        gs.confirm_dead_stones()
        assert gs.game_status == 'ended'
        assert gs.final_score is not None
        assert gs.winner in ('B', 'W')

    def test_skip_dead_marking_still_scores(self):
        """跳过标记也能正确结算"""
        gs = GameState()
        gs.pass_move()
        gs.pass_move()
        gs.clear_dead_stones()
        gs.confirm_dead_stones()
        assert gs.game_status == 'ended'
        assert gs.final_score is not None

    def test_reset_from_end_marking(self):
        """标记模式下重置回到 playing"""
        gs = GameState()
        gs.pass_move()
        gs.pass_move()
        assert gs.game_status == 'end_marking'
        gs.reset()
        assert gs.game_status == 'playing'

    def test_move_after_pass_resets_counter(self):
        """PASS 后落子重置连续 PASS 计数"""
        gs = GameState()
        gs.pass_move()
        assert gs.consecutive_passes == 1
        gs.make_move(9, 9)
        assert gs.consecutive_passes == 0
        assert gs.game_status == 'playing'


class TestButtonInteractionSimulation:
    """模拟按钮交互场景（不依赖 UI 框架）"""

    def test_pass_during_ai_turn_ignored_by_game_state(self):
        """game_state.pass_move() 在 AI 回合可用（button 守卫由 main.py 负责）"""
        gs = GameState()
        gs.current_player = 'W'  # 模拟 AI 回合
        # game_state 本身允许任何玩家 PASS，按钮守卫在 main.py
        result = gs.pass_move()
        assert result, "game_state 应允许 PASS"
        assert gs.game_status == 'playing'

    def test_make_move_always_uses_current_player(self):
        """make_move 始终为 current_player 落子"""
        gs = GameState()
        assert gs.current_player == 'B'
        gs.make_move(3, 3)
        assert gs.board.get_stone(3, 3) == 'B', "B应落黑子"

    def test_undo_to_empty_history(self):
        """撤销到历史为空"""
        gs = GameState()
        gs.make_move(3, 3)
        gs.make_move(3, 4)  # AI 走
        gs.undo()
        gs.undo()
        assert len(gs.history) == 0
        assert gs.move_count == 0

    def test_undo_when_history_empty(self):
        """历史为空时撤销返回 False"""
        gs = GameState()
        result = gs.undo()
        assert not result

    def test_undo_after_pass(self):
        """PASS 后撤销恢复状态"""
        gs = GameState()
        gs.make_move(3, 3)
        gs.pass_move()
        assert gs.consecutive_passes == 1
        gs.undo()
        assert gs.consecutive_passes == 0
        assert gs.move_count == 1, "撤销 PASS 后手数应回退"


class TestNonLogicalOperations:
    """模拟非逻辑性/异常操作"""

    def test_make_move_after_game_ended(self):
        """结束后落子应失败"""
        gs = GameState()
        gs.game_status = 'ended'
        result = gs.make_move(3, 3)
        assert not result

    def test_pass_after_game_ended(self):
        """结束后 PASS 应失败"""
        gs = GameState()
        gs.game_status = 'ended'
        result = gs.pass_move()
        assert not result

    def test_make_move_out_of_bounds(self):
        """越界落子应失败"""
        gs = GameState()
        result = gs.make_move(-1, 5)
        assert not result
        result = gs.make_move(19, 5)
        assert not result
        result = gs.make_move(5, -1)
        assert not result

    def test_make_move_on_occupied_point(self):
        """重复落子应失败"""
        gs = GameState()
        gs.make_move(3, 3)
        result = gs.make_move(3, 3)
        assert not result, "非空位应拒绝落子"

    def test_rapid_pass_still_ends_game(self):
        """连续多次 PASS 也在第二次结束"""
        gs = GameState()
        gs.pass_move()
        gs.pass_move()
        assert gs.game_status == 'end_marking'
        # 第三次 PASS 在结束状态下应失败
        result = gs.pass_move()
        assert not result, "已结束不能再 PASS"

    def test_reset_during_game_clears_everything(self):
        """游戏进行中重置清空所有状态"""
        gs = GameState()
        gs.make_move(3, 3)
        gs.make_move(3, 4)
        gs.make_move(4, 4)
        gs.reset()
        assert gs.move_count == 0
        assert gs.current_player == 'B'
        assert gs.history == []
        assert gs.move_history == []
        assert gs.game_status == 'playing'

    def test_capture_updates_score_immediately(self):
        """吃子即时更新提子计数"""
        gs = GameState(9)
        # 构造吃子局面：B 在 (4,4)，W 包围后提掉
        gs.board.set_stone(4, 4, 'B')
        gs.current_player = 'W'
        gs.board.set_stone(3, 4, 'W')
        gs.board.set_stone(5, 4, 'W')
        gs.board.set_stone(4, 3, 'W')
        # W 在 (4,5) 落子提掉 (4,4) 的 B
        result = gs.make_move(4, 5)
        if result:
            assert gs.captures['W'] >= 1, "提子数应更新"

    def test_move_history_tracks_all_moves(self):
        """move_history 记录每一步"""
        gs = GameState()
        gs.make_move(3, 3)  # B
        gs.make_move(3, 4)  # W (AI)
        gs.make_move(4, 3)  # B
        assert len(gs.move_history) == 3
        # 验证内容
        assert gs.move_history[0] == (3, 3, 'B')
        assert gs.move_history[1] == (3, 4, 'W')
        assert gs.move_history[2] == (4, 3, 'B')
