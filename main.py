import pygame
import sys
import threading
import time
import queue
from game.game_state import GameState
from ui.renderer import Renderer
from ui.components import Button, DifficultyButton, ToggleButton, UIManager
from game.ai import EasyAI, MediumAI, HardAI
from game.ko_utils import KoUtils
from game.sgf import export_to_file, import_from_file
from ui.sound import SoundManager


def main():
    pygame.init()

    screen_width = 1200
    screen_height = 800
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("围棋游戏 - Go Game")

    # --- 可配置参数 ---
    board_grid_size = 19
    board_pixel_size = 600
    board_x = 60
    board_y = (screen_height - board_pixel_size) // 2
    sidebar_x = board_x + board_pixel_size + 60
    sidebar_width = 380

    renderer = Renderer(screen, board_x, board_y, board_pixel_size, board_grid_size)
    game_state = GameState(board_grid_size)
    ui_manager = UIManager()
    sound_mgr = SoundManager()
    sound_mgr.load('place', 'assets/sounds/place.wav')
    sound_mgr.load('capture', 'assets/sounds/capture.wav')
    sound_mgr.load('pass', 'assets/sounds/pass.wav')
    sound_mgr.load('end', 'assets/sounds/end.wav')

    difficulty = 'easy'
    player_color = 'B'  # 'B'=黑, 'W'=白

    ai_instances = {
        'easy': EasyAI(),
        'medium': MediumAI(),
        'hard': HardAI()
    }
    ai = ai_instances[difficulty]

    ai_move_queue = queue.Queue()
    ai_thread = None
    ai_start_time = 0
    is_game_over = False

    show_hints = False
    show_influence = False
    show_ko_threats = True
    best_moves = []
    influence_map = []
    placed_times = {}
    ko_threats = []
    threat_scores = {}
    cached_situation = None  # 形势判断缓存
    situation_dirty = True    # 脏标记，走子后重置
    review_mode = False       # 回顾模式
    review_selected = -1      # 回顾选中的步数
    timer_enabled = False     # 计时器开关
    timer_base = 600          # 基础时间（秒）
    player_times = {'B': 600, 'W': 600}  # 双方剩余时间
    timer_running = False     # 计时器是否在走
    last_timer_tick = time.time()

    difficulty_buttons = []
    current_difficulty_buttons = []
    pass_btn = None
    undo_btn = None
    hints_btn = None

    def get_ai_color():
        return 'W' if player_color == 'B' else 'B'

    def set_difficulty(new_difficulty):
        nonlocal difficulty, ai
        difficulty = new_difficulty
        ai = ai_instances[difficulty]
        for btn in current_difficulty_buttons:
            btn.is_selected = (btn.difficulty == difficulty)

    def set_difficulty_easy():
        set_difficulty('easy')

    def set_difficulty_medium():
        set_difficulty('medium')

    def set_difficulty_hard():
        set_difficulty('hard')

    PASS_SENTINEL = ('PASS',)

    def ai_worker():
        """AI工作线程 - 仅计算走法，不修改game_state"""
        try:
            if game_state.current_player == get_ai_color() and game_state.game_status == 'playing':
                move = ai.get_move(game_state.board, game_state.current_player, game_state.rules, game_state.ko_point)
                if move is not None:
                    ai_move_queue.put(move)
                else:
                    # 通过哨兵通知主线程执行PASS，避免线程安全问题
                    ai_move_queue.put(PASS_SENTINEL)
        except Exception as e:
            print(f"AI错误: {e}")
            import traceback
            traceback.print_exc()
            ai_move_queue.put(None)

    def start_ai_thinking():
        """启动AI思考"""
        nonlocal ai_thread, ai_start_time
        if ai_thread is None or not ai_thread.is_alive():
            ai_start_time = time.time()
            ai_thread = threading.Thread(target=ai_worker)
            ai_thread.daemon = True
            ai_thread.start()

    def undo_move():
        if (game_state.game_status == 'playing' and
            game_state.current_player == player_color and
            not ai_thread):
            if len(game_state.history) >= 2:
                game_state.undo()
                game_state.undo()

    def end_game_func():
        if game_state.game_status == 'playing':
            game_state.end_game()

    def restart_game():
        nonlocal ai_thread, ai_start_time, is_game_over, best_moves, influence_map, placed_times, difficulty, ko_threats, threat_scores, cached_situation, situation_dirty
        ai_thread = None
        ai_start_time = 0
        is_game_over = False
        best_moves = []
        influence_map = []
        placed_times = {}
        ko_threats = []
        threat_scores = {}
        cached_situation = None
        situation_dirty = True
        game_state.reset()

    def pass_move_func():
        if (game_state.game_status == 'playing' and
            game_state.current_player == player_color and
            not ai_thread):
            game_state.pass_move()
            sound_mgr.play('pass')

    def confirm_dead_stones_func():
        if game_state.game_status == 'end_marking':
            game_state.confirm_dead_stones()
            sound_mgr.play('end')

    def skip_dead_marking_func():
        if game_state.game_status == 'end_marking':
            game_state.clear_dead_stones()
            game_state.confirm_dead_stones()

    def save_game_func():
        game_state.save_game()

    def load_game_func():
        nonlocal ai_thread, placed_times, renderer, board_grid_size
        ai_thread = None
        placed_times = {}
        if game_state.load_game():
            board_grid_size = game_state.board_size
            renderer = Renderer(screen, board_x, board_y, board_pixel_size, board_grid_size)

    def export_sgf_func():
        filepath = export_to_file(game_state)
        print(f"SGF exported: {filepath}")

    def import_sgf_func():
        nonlocal ai_thread, placed_times, renderer, board_grid_size
        ai_thread = None
        placed_times = {}
        result = import_from_file('data/sgf/latest.sgf')
        if result is not None:
            game_state.board = result.board
            game_state.current_player = result.current_player
            game_state.move_count = result.move_count
            game_state.captures = result.captures
            game_state.ko_point = result.ko_point
            game_state.history = result.history
            game_state.game_status = result.game_status
            game_state.consecutive_passes = result.consecutive_passes
            game_state.winner = result.winner
            game_state.final_score = result.final_score
            game_state.last_move = result.last_move
            game_state.move_history = result.move_history
            game_state.board_size = result.board_size
            board_grid_size = result.board_size
            renderer = Renderer(screen, board_x, board_y, board_pixel_size, board_grid_size)

    def enter_review_mode():
        nonlocal review_mode, review_selected
        if game_state.game_status == 'ended' and game_state.move_history:
            review_mode = True
            review_selected = len(game_state.move_history) - 1
            game_state.go_to_move(review_selected)

    def review_prev_step():
        nonlocal review_selected, review_mode
        if not review_mode:
            return
        if review_selected <= 0:
            review_mode = False
            review_selected = -1
            game_state.review_index = -1
            # 恢复到终局状态
            game_state.go_to_move(len(game_state.move_history) - 1)
            return
        review_selected -= 1
        game_state.review_prev()

    def review_next_step():
        nonlocal review_selected
        if not review_mode:
            return
        if review_selected >= len(game_state.move_history) - 1:
            return
        review_selected += 1
        game_state.review_next()

    def exit_review_mode():
        nonlocal review_mode, review_selected
        review_mode = False
        review_selected = -1
        game_state.review_index = -1
        if game_state.move_history:
            game_state.go_to_move(len(game_state.move_history) - 1)

    def restart_with_color(color):
        nonlocal player_color, ai_thread, ai_start_time, is_game_over, best_moves, influence_map, placed_times, ko_threats, threat_scores, cached_situation, situation_dirty
        player_color = color
        ai_thread = None
        ai_start_time = 0
        is_game_over = False
        best_moves = []
        influence_map = []
        placed_times = {}
        ko_threats = []
        threat_scores = {}
        cached_situation = None
        situation_dirty = True
        game_state.reset()

    def update_hints():
        nonlocal best_moves
        try:
            if game_state.game_status == 'playing' and game_state.current_player == player_color:
                best_moves = ai.get_best_moves_with_scores(
                    game_state.board,
                    game_state.current_player,
                    game_state.rules,
                    game_state.ko_point
                )
        except Exception as e:
            print(f"提示错误: {e}")
            best_moves = []

    def update_influence():
        nonlocal influence_map
        try:
            influence_map = game_state.calculate_influence_map()
        except Exception as e:
            print(f"势力图错误: {e}")
            influence_map = []

    def update_ko_threats():
        """更新劫材提示"""
        nonlocal ko_threats, threat_scores
        try:
            if game_state.game_status == 'playing' and game_state.ko_point is not None:
                ko_threats = KoUtils.find_ko_threats(game_state.board, game_state.current_player)
                threat_scores = {}
                for pos in ko_threats:
                    score = KoUtils._evaluate_ko_threat(game_state.board, pos[0], pos[1], game_state.current_player)
                    threat_scores[pos] = score
            else:
                ko_threats = []
                threat_scores = {}
        except Exception as e:
            print(f"劫材提示错误: {e}")
            ko_threats = []
            threat_scores = {}

    def toggle_hints():
        nonlocal show_hints
        show_hints = not show_hints
        if hints_btn:
            hints_btn.is_on = show_hints
            hints_btn.text = "提示: 开" if show_hints else "提示: 关"
        if show_hints:
            update_hints()

    def toggle_influence():
        nonlocal show_influence
        show_influence = not show_influence
        if show_influence:
            update_influence()

    def toggle_timer():
        nonlocal timer_enabled, player_times, timer_base, last_timer_tick
        timer_enabled = not timer_enabled
        if timer_enabled:
            player_times = {'B': timer_base, 'W': timer_base}
            last_timer_tick = time.time()

    # --- 按钮布局（精确定位，总宽 380px）---
    gap = 8
    bw2 = (380 - gap) // 2          # 双按钮：186
    bw3 = (380 - gap * 2) // 3      # 三按钮：121
    bh = 36
    rh = bh + 12
    bw = bw3                         # 121

    button_y = 35

    # 行1：难度（3个）
    for i, (diff, label, cb) in enumerate([
        ("easy", "初级", set_difficulty_easy),
        ("medium", "中级", set_difficulty_medium),
        ("hard", "高级", set_difficulty_hard)]):
        btn = DifficultyButton(sidebar_x + i * (bw + gap), button_y, bw, bh,
                              label, cb, diff, is_selected=(diff == 'easy'))
        ui_manager.add_component(btn)
        difficulty_buttons.append(btn)
        current_difficulty_buttons.append(btn)

    # 行2：PASS | 悔棋（等宽）
    button_y += rh
    pass_btn = Button(sidebar_x, button_y, bw2, bh, "PASS", pass_move_func)
    undo_btn = Button(sidebar_x + bw2 + gap, button_y, bw2, bh, "悔棋", undo_move)
    ui_manager.add_component(pass_btn)
    ui_manager.add_component(undo_btn)

    # 行3：提示 | 势力（2个等宽）
    button_y += rh
    tw = (380 - gap) // 2  # 186
    hints_btn = ToggleButton(sidebar_x, button_y, tw, bh, "提示", "提示", toggle_hints, is_on=False)
    ui_manager.add_component(hints_btn)
    influence_btn = ToggleButton(sidebar_x + tw + gap, button_y, tw, bh, "势力", "势力", toggle_influence, is_on=False)
    ui_manager.add_component(influence_btn)

    # 行4：计时 | 音效（2个等宽）
    button_y += rh
    timer_btn = ToggleButton(sidebar_x, button_y, tw, bh, "计时", "计时", toggle_timer, is_on=False)
    ui_manager.add_component(timer_btn)
    sound_btn = ToggleButton(sidebar_x + tw + gap, button_y, tw, bh,
                             "音效", "音效", lambda: sound_mgr.toggle(), is_on=True)
    ui_manager.add_component(sound_btn)

    # 行4：保存 | 读取 | SGF
    button_y += rh
    for i, (label, cb) in enumerate([
        ("保存", save_game_func), ("读取", load_game_func),
        ("SGF", export_sgf_func)]):
        btn = Button(sidebar_x + i * (bw + gap), button_y, bw, bh, label, cb)
        ui_manager.add_component(btn)

    # 行5：结束 | 重开 | 复盘
    button_y += rh
    end_game_btn = Button(sidebar_x, button_y, bw, bh, "结束", end_game_func)
    ui_manager.add_component(end_game_btn)
    restart_btn = Button(sidebar_x + bw + gap, button_y, bw, bh, "重开", restart_game)
    ui_manager.add_component(restart_btn)
    review_btn = Button(sidebar_x + (bw + gap) * 2, button_y, bw, bh, "复盘", enter_review_mode)
    ui_manager.add_component(review_btn)

    # 行6：执色 + 死子按钮（同排）
    button_y += rh
    color_toggle_btn = ToggleButton(sidebar_x, button_y, bw2, bh,
                                    "执黑", "执白",
                                    lambda: restart_with_color('W' if player_color == 'B' else 'B'),
                                    is_on=True)
    color_toggle_btn.text_on = "执黑"
    color_toggle_btn.text_off = "执白"
    color_toggle_btn.text = "执黑"
    ui_manager.add_component(color_toggle_btn)

    confirm_dead_btn = Button(sidebar_x + bw2 + gap, button_y, bw2, bh,
                              "确认死子", confirm_dead_stones_func)
    skip_dead_btn = Button(sidebar_x, button_y, bw2, bh,
                           "跳过标记", skip_dead_marking_func)
    confirm_dead_btn.active = False
    skip_dead_btn.active = False
    ui_manager.add_component(confirm_dead_btn)
    ui_manager.add_component(skip_dead_btn)

    # 游戏信息面板起始位置（硬编码：按钮区域结束≈370，面板从380开始）
    game_state_panel_y = 380
    review_overlay_buttons = []

    _last_btn_state = {}

    def update_button_states():
        """更新按钮状态（带防抖：仅状态变化时更新颜色）"""
        nonlocal _last_btn_state
        ai_busy = ai_thread is not None and ai_thread.is_alive()
        in_marking = game_state.game_status == 'end_marking'
        is_ended = game_state.game_status == 'ended'

        can_player_act = (game_state.game_status == 'playing' and
                         game_state.current_player == player_color and
                         not ai_busy)
        can_undo = (game_state.game_status == 'playing' and
                   not ai_busy and
                   len(game_state.history) >= 2)
        new_state = {
            'pass': can_player_act,
            'undo': can_undo,
            'confirm': in_marking,
            'skip': in_marking,
            'review': is_ended and bool(game_state.move_history),
            'ai': ai_busy,
        }
        if new_state == _last_btn_state:
            return
        _last_btn_state = new_state

        if pass_btn:
            pass_btn.active = can_player_act
        if undo_btn:
            undo_btn.active = can_undo
        for btn in difficulty_buttons:
            btn.active = not ai_busy and game_state.game_status == 'playing'
        confirm_dead_btn.active = in_marking
        confirm_dead_btn.visible = in_marking
        skip_dead_btn.active = in_marking
        skip_dead_btn.visible = in_marking
        review_btn.active = is_ended and bool(game_state.move_history)
        # 执色按钮文字始终更新
        if color_toggle_btn:
            color_toggle_btn.is_on = (player_color == 'B')
            color_toggle_btn.text = "执黑" if player_color == 'B' else "执白"

    clock = pygame.time.Clock()
    running = True

    last_hint_update = 0
    hint_update_interval = 1.0

    print("围棋游戏启动！")
    print(f"棋盘: {board_grid_size}x{board_grid_size}, 难度: {difficulty}, 执色: {'黑' if player_color == 'B' else '白'}")

    while running:
        dt = clock.tick(60) / 1000.0
        events = []

        for event in pygame.event.get():
            events.append(event)
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if review_mode:
                    if event.key == pygame.K_LEFT:
                        review_prev_step()
                    elif event.key == pygame.K_RIGHT:
                        review_next_step()
                    elif event.key == pygame.K_ESCAPE:
                        exit_review_mode()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    # 终局覆盖层按钮
                    if game_state.game_status == 'ended':
                        btns = renderer._overlay_buttons
                        pos = event.pos
                        if btns.get('restart') and btns['restart'].collidepoint(pos):
                            restart_game()
                            continue
                        if btns.get('review') and btns['review'].collidepoint(pos):
                            if game_state.move_history:
                                enter_review_mode()
                            continue

                    board_pos = renderer.screen_to_board(event.pos)
                    if board_pos is not None:
                        x, y = board_pos
                        # 死子标记模式
                        if game_state.game_status == 'end_marking':
                            if not game_state.board.is_empty(x, y):
                                game_state.mark_dead_stone(x, y)
                            continue
                        ai_busy = ai_thread is not None and ai_thread.is_alive()
                        if (game_state.game_status == 'playing' and
                            game_state.current_player == player_color and
                            not ai_busy):
                            x, y = board_pos
                            if game_state.make_move(x, y):
                                situation_dirty = True
                                placed_times[(x, y)] = renderer.animation_time
                                sound_mgr.play('place')
                                screen_pos = renderer.board_to_screen(x, y)
                                if screen_pos:
                                    renderer.add_place_particle(screen_pos[0], screen_pos[1], (255, 220, 150))
                                if show_hints:
                                    best_moves = []
                                if show_influence:
                                    update_influence()
                                update_ko_threats()

        ai_busy = ai_thread is not None and ai_thread.is_alive()

        ai_color = get_ai_color()
        if (not ai_busy and
            game_state.current_player == ai_color and
            game_state.game_status == 'playing' and
            ai_move_queue.empty()):
            start_ai_thinking()

        if not ai_busy and not ai_move_queue.empty():
            try:
                move = ai_move_queue.get_nowait()
                if move is PASS_SENTINEL:
                    game_state.pass_move()
                    situation_dirty = True
                    sound_mgr.play('pass')
                elif move is not None:
                    x, y = move
                    if game_state.make_move(x, y):
                        situation_dirty = True
                        placed_times[(x, y)] = renderer.animation_time
                        sound_mgr.play('place')
                        screen_pos = renderer.board_to_screen(x, y)
                        if screen_pos:
                            renderer.add_place_particle(screen_pos[0], screen_pos[1], (200, 200, 220))
                    if show_hints:
                        best_moves = []
                    if show_influence:
                        update_influence()
                    update_ko_threats()
                ai_thread = None
            except queue.Empty:
                pass

        # 计时器
        current_time = time.time()
        if timer_enabled and game_state.game_status == 'playing':
            dt_timer = current_time - last_timer_tick
            last_timer_tick = current_time
            cp = game_state.current_player
            player_times[cp] -= dt_timer
            if player_times[cp] <= 0:
                player_times[cp] = 0
                game_state.game_status = 'ended'
                game_state.winner = 'W' if cp == 'B' else 'B'
                game_state.final_score = None
        elif game_state.game_status != 'playing':
            timer_running = False

        ai_busy = ai_thread is not None and ai_thread.is_alive()
        if (show_hints and
            game_state.game_status == 'playing' and
            game_state.current_player == player_color and
            not best_moves and
            current_time - last_hint_update > hint_update_interval and
            not ai_busy):
            update_hints()
            last_hint_update = current_time

        update_button_states()

        ui_manager.handle_events(events)
        ui_manager.update(dt)
        renderer.update(dt)

        renderer.draw_board(screen)
        renderer.draw_coordinates(screen)

        if show_influence and influence_map:
            renderer.draw_influence_map(screen, influence_map)

        renderer.draw_star_points(screen)

        # 绘制最后落子标记
        renderer.draw_last_move(screen, game_state.last_move)

        ai_busy = ai_thread is not None and ai_thread.is_alive()
        if (show_hints and
            best_moves and
            game_state.current_player == player_color and
            game_state.game_status == 'playing' and
            not ai_busy):
            renderer.draw_hints(screen, best_moves)

        if show_ko_threats and ko_threats and game_state.game_status == 'playing':
            renderer.draw_ko_threats(screen, ko_threats, threat_scores)

        renderer.draw_pieces(screen, game_state.board, placed_times)
        ui_manager.draw(screen)

        # 下方面板：左=游戏状态 | 右=形势判断（同排），计时在下方托举
        pw = 178
        g2 = 4
        panely = game_state_panel_y
        # 游戏状态（左）—— 高度自适应，缩短到140px
        ph = 165  # 面板统一高度
        renderer.draw_current_player(screen, game_state.current_player, game_state.move_count,
                                     game_state.captures, game_state.game_status,
                                     game_state.winner, game_state.final_score,
                                     info_y=panely, info_x=sidebar_x, panel_width=pw, panel_height=ph)

        # 形势判断（右）
        if game_state.game_status == 'playing':
            if situation_dirty or cached_situation is None:
                cached_situation = game_state.estimate_situation()
                situation_dirty = False
            renderer.draw_situation_eval(screen, cached_situation['win_rate'],
                                        cached_situation['territory'],
                                        sidebar_x + pw + g2, panely,
                                        panel_width=pw, panel_height=ph)

        # 计时在下方托举，对齐侧边栏
        timer_top = panely + ph + 25
        if ai_busy:
            elapsed = time.time() - ai_start_time if ai_start_time > 0 else 0
            renderer.draw_ai_thinking(screen, sidebar_x, timer_top, 260, elapsed)
        elif timer_enabled:
            renderer.draw_timer(screen, player_times, sidebar_x, timer_top, panel_width=360)
        elif game_state.game_status == 'end_marking':
            renderer.draw_dead_stone_markers(screen, game_state.dead_stones)
            # 显示提示
            mark_font = pygame.font.Font(None, 30)
            if not hasattr(renderer, '_mark_font'):
                from ui.renderer import get_chinese_font
                renderer._mark_font = get_chinese_font(28)
            hint_surf = renderer._mark_font.render("点击棋子标记死子，完成后点「确认死子」", True, (255, 223, 128))
            hint_rect = hint_surf.get_rect(center=(screen_width // 2, screen_height - 60))
            screen.blit(hint_surf, hint_rect)
        elif game_state.game_status == 'ended' and not review_mode:
            renderer.draw_territory_overlay(screen, game_state.final_score, game_state.board)
            renderer.draw_game_over_overlay(screen, game_state.winner, game_state.final_score, game_state.move_count)

        # 回顾模式绘制
        if review_mode:
            renderer.draw_review_overlay(screen, game_state.move_history, review_selected, game_state_panel_y, sidebar_x)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
