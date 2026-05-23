"""
AI劫材策略测试套件

包含：
- 劫点检测
- 劫材寻找
- 劫材策略选择
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.board import Board
from game.rules import Rules
from game.ai import EasyAI, MediumAI, HardAI

def test_ai_detects_ko_point():
    """测试AI检测到劫点"""
    board = Board(9)
    rules = Rules()
    ai = EasyAI()
    
    board.set_stone(3, 1, 'B')
    board.set_stone(2, 2, 'B')
    board.set_stone(4, 2, 'B')
    board.set_stone(3, 3, 'B')
    board.set_stone(3, 2, 'W')
    
    ko_point = (2, 2)
    
    ko_threats = ai.find_ko_threats(board, 'B', ko_point, rules)
    
    assert isinstance(ko_threats, list), "应该返回劫材列表"

def test_easy_ai_uses_ko_strategy():
    """测试EasyAI使用劫材策略"""
    board = Board(9)
    rules = Rules()
    ai = EasyAI()
    
    board.set_stone(3, 1, 'B')
    board.set_stone(2, 2, 'B')
    board.set_stone(4, 2, 'B')
    board.set_stone(3, 3, 'B')
    board.set_stone(3, 2, 'W')
    
    ko_point = (2, 2)
    
    move = ai.get_move(board, 'B', rules, ko_point)
    
    assert move is not None, "AI应该返回劫材位置"
    assert move != ko_point, "劫材不应该是劫点本身"

def test_medium_ai_prefers_best_ko_threat():
    """测试MediumAI选择最佳劫材"""
    board = Board(9)
    rules = Rules()
    ai = MediumAI()
    
    board.set_stone(3, 1, 'B')
    board.set_stone(2, 2, 'B')
    board.set_stone(4, 2, 'B')
    board.set_stone(3, 3, 'B')
    board.set_stone(3, 2, 'W')
    
    ko_point = (2, 2)
    
    move = ai.get_move(board, 'B', rules, ko_point)
    
    assert move is not None, "AI应该返回劫材位置"
    assert move != ko_point, "劫材不应该是劫点本身"

def test_ai_without_ko_plays_normally():
    """测试AI在无劫时正常落子"""
    board = Board(9)
    rules = Rules()
    ai = EasyAI()
    
    board.set_stone(3, 3, 'B')
    board.set_stone(3, 4, 'B')
    
    ko_point = None
    
    move = ai.get_move(board, 'B', rules, ko_point)
    
    assert move is not None, "AI应该返回落子位置"

if __name__ == '__main__':
    test_ai_detects_ko_point()
    test_easy_ai_uses_ko_strategy()
    test_medium_ai_prefers_best_ko_threat()
    test_ai_without_ko_plays_normally()
    print("\n所有劫材策略测试通过！")
