"""
按钮互动测试
模拟 main.py 中 update_button_states() 的逻辑，
覆盖各种游戏状态下每个按钮的启用/禁用状态。
"""

import pytest


class ButtonState:
    """模拟 UI 按钮的状态"""
    def __init__(self, name):
        self.name = name
        self.active = True

    def set_active(self, condition):
        self.active = condition


class ButtonStateManager:
    """模拟 main.py 中的 update_button_states() 逻辑"""

    def __init__(self):
        self.pass_btn = ButtonState("PASS")
        self.undo_btn = ButtonState("悔棋")
        self.difficulty_btns = [ButtonState("初级"), ButtonState("中级"), ButtonState("高级")]
        self.board_size_btns = [ButtonState("9x9"), ButtonState("13x13"), ButtonState("19x19")]
        self.confirm_dead_btn = ButtonState("确认死子")
        self.skip_dead_btn = ButtonState("跳过标记")
        self.review_btn = ButtonState("复盘")
        self.color_toggle_btn = ButtonState("执色切换")
        self.hints_btn = ButtonState("提示")
        self.influence_btn = ButtonState("势力")
        self.timer_btn = ButtonState("计时")
        self.sound_btn = ButtonState("音效")
        self.end_game_btn = ButtonState("结束游戏")
        self.restart_btn = ButtonState("重新开始")
        self.save_btn = ButtonState("保存")
        self.load_btn = ButtonState("读取")
        self.sgf_export_btn = ButtonState("导出SGF")

    def update(self, game_status, current_player, player_color, ai_busy, history_len, has_move_history):
        """根据游戏状态更新所有按钮"""
        is_playing = game_status == 'playing'
        is_end_marking = game_status == 'end_marking'
        is_ended = game_status == 'ended'
        can_player_act = is_playing and current_player == player_color and not ai_busy

        # PASS: 只能在自己回合且 AI 空闲时使用
        self.pass_btn.set_active(can_player_act)

        # 悔棋: 游戏中、AI 空闲、历史>=2
        can_undo = is_playing and not ai_busy and history_len >= 2
        self.undo_btn.set_active(can_undo)

        # 难度按钮: 游戏中、AI 空闲
        for btn in self.difficulty_btns:
            btn.set_active(not ai_busy and is_playing)

        # 棋盘大小按钮: AI 空闲时可用
        for btn in self.board_size_btns:
            btn.set_active(not ai_busy)

        # 死子标记按钮: 仅在标记模式
        self.confirm_dead_btn.set_active(is_end_marking)
        self.skip_dead_btn.set_active(is_end_marking)

        # 复盘: 游戏结束时且有历史
        self.review_btn.set_active(is_ended and has_move_history)

        # 以下按钮始终启用
        self.color_toggle_btn.set_active(True)
        self.hints_btn.set_active(True)
        self.influence_btn.set_active(True)
        self.timer_btn.set_active(True)
        self.sound_btn.set_active(True)
        self.end_game_btn.set_active(True)
        self.restart_btn.set_active(True)
        self.save_btn.set_active(True)
        self.load_btn.set_active(True)
        self.sgf_export_btn.set_active(True)


class TestButtonStates:
    """按钮状态测试"""

    @pytest.fixture
    def mgr(self):
        return ButtonStateManager()

    def check(self, mgr, **expected):
        """辅助：验证多个按钮的 active 状态"""
        for btn_name, expected_active in expected.items():
            btn = getattr(mgr, btn_name)
            assert btn.active == expected_active, \
                f"按钮 {btn_name} 应为 {'启用' if expected_active else '禁用'}，但当前为 {'启用' if btn.active else '禁用'}"

    # ============ 正常游戏进行中 ============

    def test_playing_player_turn_no_ai(self, mgr):
        """正常游戏：玩家回合，AI 空闲"""
        mgr.update(game_status='playing', current_player='B', player_color='B',
                   ai_busy=False, history_len=5, has_move_history=True)
        self.check(mgr,
            pass_btn=True, undo_btn=True,
            confirm_dead_btn=False, skip_dead_btn=False, review_btn=False,
        )
        for btn in mgr.difficulty_btns:
            assert btn.active  # 难度按钮应启用

    def test_playing_player_turn_no_history(self, mgr):
        """刚开局：无历史，悔棋禁用"""
        mgr.update(game_status='playing', current_player='B', player_color='B',
                   ai_busy=False, history_len=0, has_move_history=False)
        self.check(mgr,
            pass_btn=True, undo_btn=False,  # 历史不足2步
        )

    def test_playing_player_turn_one_move(self, mgr):
        """只有一步历史：悔棋禁用"""
        mgr.update(game_status='playing', current_player='B', player_color='B',
                   ai_busy=False, history_len=1, has_move_history=True)
        self.check(mgr,
            pass_btn=True, undo_btn=False,  # 需要至少2步才能悔棋
        )

    # ============ AI 思考中 ============

    def test_ai_thinking_player_wait(self, mgr):
        """AI 思考中：所有玩家操作按钮禁用"""
        mgr.update(game_status='playing', current_player='W', player_color='B',
                   ai_busy=True, history_len=5, has_move_history=True)
        self.check(mgr,
            pass_btn=False,          # AI 回合
            undo_btn=False,          # AI 忙碌
            confirm_dead_btn=False,
        )
        for btn in mgr.difficulty_btns:
            assert not btn.active, "AI 忙碌时难度按钮应禁用"

    def test_ai_thinking_player_color_mismatch(self, mgr):
        """AI 回合但 AI 线程未启动：按钮应禁用"""
        mgr.update(game_status='playing', current_player='W', player_color='B',
                   ai_busy=False, history_len=5, has_move_history=True)
        self.check(mgr,
            pass_btn=False,    # 轮到 W，玩家是 B
            undo_btn=True,     # 历史>=2 且 AI 空闲
        )

    # ============ 玩家执白 ============

    def test_white_player_own_turn(self, mgr):
        """玩家执白且轮到白方"""
        mgr.update(game_status='playing', current_player='W', player_color='W',
                   ai_busy=False, history_len=3, has_move_history=True)
        self.check(mgr,
            pass_btn=True,      # 玩家回合
            undo_btn=True,
        )

    def test_white_player_ai_black_turn(self, mgr):
        """玩家执白但轮到黑方(AI)：按钮禁用"""
        mgr.update(game_status='playing', current_player='B', player_color='W',
                   ai_busy=False, history_len=3, has_move_history=True)
        self.check(mgr,
            pass_btn=False,     # 轮到 AI
        )

    # ============ 终局标记模式 ============

    def test_end_marking_mode(self, mgr):
        """死子标记模式"""
        mgr.update(game_status='end_marking', current_player='B', player_color='B',
                   ai_busy=False, history_len=10, has_move_history=True)
        self.check(mgr,
            pass_btn=False,           # 游戏已结束
            undo_btn=False,           # 游戏已结束
            confirm_dead_btn=True,    # 标记模式可用
            skip_dead_btn=True,
            review_btn=False,         # 还未最终结束
        )

    def test_end_marking_with_history(self, mgr):
        """标记模式：难度按钮应禁用"""
        mgr.update(game_status='end_marking', current_player='B', player_color='B',
                   ai_busy=False, history_len=10, has_move_history=True)
        for btn in mgr.difficulty_btns:
            assert not btn.active, "标记模式难度按钮应禁用"

    # ============ 游戏已结束 ============

    def test_game_ended_with_history(self, mgr):
        """游戏结束且有历史：复盘可用"""
        mgr.update(game_status='ended', current_player='B', player_color='B',
                   ai_busy=False, history_len=20, has_move_history=True)
        self.check(mgr,
            pass_btn=False,
            undo_btn=False,
            confirm_dead_btn=False,
            skip_dead_btn=False,
            review_btn=True,          # 可复盘
        )

    def test_game_ended_no_history(self, mgr):
        """游戏结束但无历史：复盘禁用"""
        mgr.update(game_status='ended', current_player='B', player_color='B',
                   ai_busy=False, history_len=0, has_move_history=False)
        self.check(mgr,
            review_btn=False,         # 无历史不可复盘
        )

    # ============ 多条件组合 ============

    def test_undo_requires_min_two_history(self, mgr):
        """悔棋需要至少2步历史，不受玩家颜色影响"""
        mgr.update(game_status='playing', current_player='B', player_color='B',
                   ai_busy=False, history_len=0, has_move_history=False)
        assert not mgr.undo_btn.active

        mgr.update(game_status='playing', current_player='B', player_color='B',
                   ai_busy=False, history_len=1, has_move_history=True)
        assert not mgr.undo_btn.active

        mgr.update(game_status='playing', current_player='B', player_color='B',
                   ai_busy=False, history_len=2, has_move_history=True)
        assert mgr.undo_btn.active

    def test_pass_requires_player_turn_and_no_ai(self, mgr):
        """PASS 需要是玩家回合且 AI 空闲"""
        # AI 忙碌
        mgr.update(game_status='playing', current_player='B', player_color='B',
                   ai_busy=True, history_len=5, has_move_history=True)
        assert not mgr.pass_btn.active

        # AI 空闲但不是玩家回合
        mgr.update(game_status='playing', current_player='W', player_color='B',
                   ai_busy=False, history_len=5, has_move_history=True)
        assert not mgr.pass_btn.active

        # 玩家回合且 AI 空闲
        mgr.update(game_status='playing', current_player='B', player_color='B',
                   ai_busy=False, history_len=5, has_move_history=True)
        assert mgr.pass_btn.active

    def test_dead_marking_only_in_marking_mode(self, mgr):
        """死子按钮仅在标记模式启用"""
        mgr.update(game_status='playing', current_player='B', player_color='B',
                   ai_busy=False, history_len=5, has_move_history=True)
        assert not mgr.confirm_dead_btn.active
        assert not mgr.skip_dead_btn.active

        mgr.update(game_status='end_marking', current_player='B', player_color='B',
                   ai_busy=False, history_len=5, has_move_history=True)
        assert mgr.confirm_dead_btn.active
        assert mgr.skip_dead_btn.active

        mgr.update(game_status='ended', current_player='B', player_color='B',
                   ai_busy=False, history_len=5, has_move_history=True)
        assert not mgr.confirm_dead_btn.active
        assert not mgr.skip_dead_btn.active

    def test_review_only_when_ended_with_moves(self, mgr):
        """复盘仅在结束且有走法时可用"""
        mgr.update(game_status='playing', current_player='B', player_color='B',
                   ai_busy=False, history_len=5, has_move_history=True)
        assert not mgr.review_btn.active

        mgr.update(game_status='ended', current_player='B', player_color='B',
                   ai_busy=False, history_len=5, has_move_history=True)
        assert mgr.review_btn.active

        mgr.update(game_status='ended', current_player='B', player_color='B',
                   ai_busy=False, history_len=0, has_move_history=False)
        assert not mgr.review_btn.active

    def test_difficulty_disabled_during_ai(self, mgr):
        """AI 思考时难度按钮禁用"""
        mgr.update(game_status='playing', current_player='W', player_color='B',
                   ai_busy=True, history_len=5, has_move_history=True)
        for btn in mgr.difficulty_btns:
            assert not btn.active

        mgr.update(game_status='playing', current_player='B', player_color='B',
                   ai_busy=False, history_len=5, has_move_history=True)
        for btn in mgr.difficulty_btns:
            assert btn.active

    # ============ 始终启用的按钮 ============

    def test_always_enabled_buttons(self, mgr):
        """始终可用的按钮"""
        for status in ['playing', 'end_marking', 'ended']:
            for ai_on in [True, False]:
                mgr.update(game_status=status, current_player='B', player_color='B',
                          ai_busy=ai_on, history_len=5, has_move_history=True)
                assert mgr.color_toggle_btn.active
                assert mgr.hints_btn.active
                assert mgr.influence_btn.active
                assert mgr.timer_btn.active
                assert mgr.sound_btn.active
                assert mgr.end_game_btn.active
                assert mgr.restart_btn.active
                assert mgr.save_btn.active
                assert mgr.load_btn.active
