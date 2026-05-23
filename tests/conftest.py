"""测试共享配置与夹具"""
import sys
import os
import pytest

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.board import Board
from game.rules import Rules
from game.game_state import GameState


@pytest.fixture
def board():
    """9x9 棋盘夹具"""
    return Board(9)


@pytest.fixture
def rules():
    """规则实例"""
    return Rules()


@pytest.fixture
def game_state():
    """游戏状态实例"""
    return GameState()
