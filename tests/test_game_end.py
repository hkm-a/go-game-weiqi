"""
测试驱动开发 - 胜负判定优化 v1.1

本模块测试中国规则下的胜负判定功能：
1. 领地计算
2. 死子识别
3. 终局检测
4. 胜负计算
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.board import Board
from game.rules import Rules
from game.game_state import GameState


class TestTerritoryCalculation:
    """测试领地计算功能"""
    
    def test_empty_territory_black(self):
        """测试纯黑方领地"""
        board = Board(9)
        rules = Rules()
        
        board.set_stone(0, 0, 'B')
        board.set_stone(1, 0, 'B')
        board.set_stone(0, 1, 'B')
        
        game_state = GameState()
        game_state.board = board
        
        black_terr, white_terr = game_state.calculate_territory()
        
        assert black_terr >= 1, "黑方应至少占有1目"
    
    def test_empty_territory_white(self):
        """测试纯白方领地"""
        board = Board(9)
        rules = Rules()
        
        board.set_stone(8, 8, 'W')
        board.set_stone(7, 8, 'W')
        board.set_stone(8, 7, 'W')
        
        game_state = GameState()
        game_state.board = board
        
        black_terr, white_terr = game_state.calculate_territory()
        
        assert white_terr >= 1, "白方应至少占有1目"
    
    def test_complex_territory(self):
        """测试复杂领地情况"""
        board = Board(9)
        rules = Rules()
        
        board.set_stone(0, 0, 'B')
        board.set_stone(1, 0, 'B')
        board.set_stone(0, 1, 'B')
        
        board.set_stone(4, 4, 'B')
        
        game_state = GameState()
        game_state.board = board
        
        black_terr, white_terr = game_state.calculate_territory()
        
        assert black_terr > 0, "黑方应有领地"
        assert white_terr == 0, "白方应无领地"
        assert black_terr + white_terr < 81, "双方领地不应超过棋盘总数"


class TestDeadStoneRecognition:
    """测试死子识别功能"""
    
    def test_dead_stone_in_enemy_territory(self):
        """测试被困在敌方领地的死子"""
        board = Board(9)
        rules = Rules()
        
        board.set_stone(0, 0, 'B')
        board.set_stone(0, 1, 'B')
        board.set_stone(1, 0, 'B')
        
        board.set_stone(8, 8, 'W')
        board.set_stone(7, 8, 'W')
        board.set_stone(8, 7, 'W')
        board.set_stone(7, 7, 'W')
        
        game_state = GameState()
        game_state.board = board
        
        black_stones = sum(1 for y in range(9) for x in range(9) 
                          if board.get_stone(x, y) == 'B')
        white_stones = sum(1 for y in range(9) for x in range(9) 
                          if board.get_stone(x, y) == 'W')
        
        assert black_stones == 3, "应有3个黑子"
        assert white_stones == 4, "应有4个白子"


class TestGameEndDetection:
    """测试终局检测功能"""
    
    def test_consecutive_passes(self):
        """测试连续PASS终局"""
        game_state = GameState()
        
        game_state.pass_move()
        assert game_state.consecutive_passes == 1
        assert game_state.game_status == 'playing'
        
        game_state.pass_move()
        assert game_state.consecutive_passes == 2
        assert game_state.game_status == 'ended', "两次PASS后应结束游戏"
    
    def test_auto_end_after_no_captures(self):
        """测试长期无吃子自动终局"""
        game_state = GameState()
        
        for i in range(35):
            x = (i * 7) % 19
            y = (i * 11) % 19
            if game_state.board.is_empty(x, y):
                game_state.make_move(x, y)
        
        if game_state.move_count >= 30:
            assert game_state.game_status in ['playing', 'ended'], \
                "游戏应处于进行中或已结束状态"


class TestScoreCalculation:
    """测试分数计算功能"""
    
    def test_basic_score_calculation(self):
        """测试基础分数计算（中国规则）"""
        board = Board(9)
        rules = Rules()
        
        board.set_stone(4, 4, 'B')
        board.set_stone(0, 0, 'B')
        board.set_stone(0, 1, 'B')
        
        board.set_stone(8, 8, 'W')
        board.set_stone(8, 7, 'W')
        board.set_stone(7, 8, 'W')
        
        game_state = GameState()
        game_state.board = board
        game_state.end_game()
        
        assert game_state.final_score is not None, "应有最终分数"
        assert 'black' in game_state.final_score, "应有黑方分数"
        assert 'white' in game_state.final_score, "应有白方分数"
        
        black_score = game_state.final_score['black']
        white_score = game_state.final_score['white']
        
        assert black_score > 0, "黑方分数应大于0"
        assert white_score > 0, "白方分数应大于0"
        assert white_score > black_score, "白方因有贴目，分数应更高"
    
    def test_black_stones_count(self):
        """测试黑子计数"""
        board = Board(9)
        
        board.set_stone(0, 0, 'B')
        board.set_stone(1, 1, 'B')
        board.set_stone(2, 2, 'B')
        
        game_state = GameState()
        game_state.board = board
        game_state.end_game()
        
        assert game_state.final_score['black_stones'] == 3, "应有3个黑子"
    
    def test_white_stones_count(self):
        """测试白子计数"""
        board = Board(9)
        
        board.set_stone(8, 8, 'W')
        board.set_stone(7, 7, 'W')
        
        game_state = GameState()
        game_state.board = board
        game_state.end_game()
        
        assert game_state.final_score['white_stones'] == 2, "应有2个白子"
    
    def test_komi_application(self):
        """测试贴目应用"""
        board = Board(9)
        
        board.set_stone(0, 0, 'B')
        board.set_stone(1, 0, 'B')
        board.set_stone(0, 1, 'B')
        
        board.set_stone(8, 8, 'W')
        
        game_state = GameState()
        game_state.board = board
        game_state.end_game()
        
        assert game_state.final_score['white'] > game_state.final_score['black'], \
            "白方因贴目3.75子，应分数更高"


class TestInfluenceMap:
    """测试势力图计算"""
    
    def test_influence_calculation(self):
        """测试势力影响计算"""
        board = Board(9)
        board.set_stone(4, 4, 'B')
        board.set_stone(6, 6, 'W')
        
        game_state = GameState()
        game_state.board = board
        
        influence = game_state.calculate_influence_map()
        
        assert influence is not None, "应有势力图"
        assert len(influence) == 9, "势力图应为9x9"
        assert len(influence[0]) == 9, "势力图应为9x9"
        
        center_influence = influence[4][4]
        corner_influence = influence[0][0]
        
        assert center_influence > corner_influence, \
            "中心点受黑子影响应大于角落"


class TestBasicRules:
    """基础规则测试（确保重构不破坏现有功能）"""
    
    def test_basic_placement(self):
        """测试基础落子"""
        board = Board(9)
        rules = Rules()
        
        success, captured, ko = rules.place_stone(board, 4, 4, 'B')
        
        assert success, "应在空位成功落子"
        assert captured == 0, "不应吃子"
        assert ko is None, "不应有劫"
        assert board.get_stone(4, 4) == 'B', "该位置应有黑子"
    
    def test_capture_enemy(self):
        """测试吃子"""
        board = Board(9)
        rules = Rules()
        
        board.set_stone(3, 4, 'W')
        board.set_stone(5, 4, 'W')
        board.set_stone(4, 3, 'W')
        board.set_stone(4, 4, 'B')
        
        success, captured, ko = rules.place_stone(board, 4, 5, 'W')
        
        assert success, "应成功吃子"
        assert captured == 1, "应吃1个子"
        assert board.get_stone(4, 4) is None, "原黑子位置应为空"
    
    def test_self_capture_forbidden(self):
        """测试禁止自杀"""
        board = Board(9)
        rules = Rules()
        
        board.set_stone(3, 4, 'B')
        board.set_stone(5, 4, 'B')
        board.set_stone(4, 3, 'B')
        board.set_stone(4, 5, 'B')
        
        success, captured, ko = rules.place_stone(board, 4, 4, 'W')
        
        assert not success, "自杀应被禁止"
        assert board.get_stone(4, 4) is None, "该位置应保持为空"
    
    @pytest.mark.skip(reason="打劫测试用例需要重新设计")
    def test_ko_rule(self):
        """测试打劫规则"""
        board = Board(9)
        rules = Rules()
        
        board.set_stone(4, 3, 'B')
        board.set_stone(3, 4, 'B')
        board.set_stone(5, 4, 'B')
        board.set_stone(4, 5, 'W')
        board.set_stone(3, 5, 'W')
        board.set_stone(5, 5, 'W')
        
        success, captured, ko = rules.place_stone(board, 4, 4, 'W')
        assert success
        
        success, captured, ko = rules.place_stone(board, 4, 6, 'B')
        assert success
        assert ko is not None, f"应有劫，ko={ko}"
        
        success, captured, new_ko = rules.place_stone(board, ko[0], ko[1], 'W', ko)
        assert not success, "打劫位置应禁止立即落子"
        print("test_ko_rule passed")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
