"""SGF 棋谱格式导入/导出模块"""
import os
from game.board import Board
from game.game_state import GameState


def _coord_to_sgf(x, y):
    """将棋盘坐标 (x, y) 转换为 SGF 字母坐标（a=0, b=1, ..., 跳过 i）"""
    def to_letter(n):
        return chr(ord('a') + n) if n < 8 else chr(ord('a') + n + 1)
    return to_letter(x) + to_letter(y)


def _sgf_to_coord(s, board_size):
    """将 SGF 字母坐标转换为棋盘坐标 (x, y)"""
    def to_num(c):
        n = ord(c) - ord('a')
        return n if n < 9 else n - 1  # 跳过 i
    if len(s) < 2:
        return None
    return (to_num(s[0]), to_num(s[1]))


def export_sgf(game_state, filename=None):
    """导出 SGF 棋谱字符串

    Args:
        game_state: 游戏状态
        filename: 可选，如果提供则写入文件

    Returns:
        SGF 格式字符串
    """
    lines = ['(;FF[4]GM[1]', f'SZ[{game_state.board_size}]', 'KM[3.75]', 'RU[Chinese]']

    # 胜负结果
    if game_state.game_status == 'ended' and game_state.winner:
        if game_state.final_score:
            diff = abs(game_state.final_score['black'] - game_state.final_score['white'])
            lines.append(f'RE[{game_state.winner}+{diff:.1f}]')
        else:
            lines.append(f'RE[{game_state.winner}+]')
    lines.append('PB[Player]')
    lines.append('PW[AI]')

    # 走法序列
    for mx, my, mc in game_state.move_history:
        color = 'B' if mc == 'B' else 'W'
        if mx is None:
            lines.append(f';{color}[]')
        else:
            lines.append(f';{color}[{_coord_to_sgf(mx, my)}]')

    lines.append(')')
    return ''.join(lines)


def import_sgf(sgf_text, board_size=19):
    """从 SGF 文本导入棋局

    Args:
        sgf_text: SGF 格式字符串
        board_size: 棋盘尺寸

    Returns:
        GameState 实例，解析失败返回 None
    """
    game_state = GameState(board_size)

    # 提取所有 ;B[xxx] 和 ;W[xxx] 节点
    moves = []
    i = 0
    while i < len(sgf_text):
        if sgf_text[i] == ';':
            i += 1
            color = ''
            while i < len(sgf_text) and sgf_text[i] in 'BW':
                color += sgf_text[i]
                i += 1
            if color in ('B', 'W'):
                # 读取坐标
                if i < len(sgf_text) and sgf_text[i] == '[':
                    i += 1
                    coord = ''
                    while i < len(sgf_text) and sgf_text[i] != ']':
                        coord += sgf_text[i]
                        i += 1
                    moves.append((color, coord if coord else None))
                    if i < len(sgf_text):
                        i += 1
                else:
                    i += 1
        else:
            i += 1

    # 执行走法
    for color, coord in moves:
        if coord is None:
            game_state.pass_move()
        else:
            xy = _sgf_to_coord(coord, board_size)
            if xy is None:
                continue
            x, y = xy
            if not game_state.make_move(x, y):
                pass  # 跳过无效走法（如禁着点）

    return game_state


def export_to_file(game_state, filepath='data/sgf/latest.sgf'):
    """导出 SGF 到文件"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    sgf = export_sgf(game_state)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(sgf)
    return filepath


def import_from_file(filepath):
    """从 SGF 文件导入"""
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'r', encoding='utf-8') as f:
        sgf = f.read()
    return import_sgf(sgf)
