import pygame
import sys
import threading
import time
import queue
from game.game_state import GameState
from ui.renderer import Renderer
from ui.components import Button, DifficultyButton, ToggleButton, UIManager
from game.ai import EasyAI, MediumAI, HardAI

def main():
    pygame.init()
    
    screen_width = 1150
    screen_height = 780
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("围棋游戏 - Go Game")
    
    board_size = 600
    board_x = 30
    board_y = (screen_height - board_size) // 2
    
    sidebar_x = board_x + board_size + 50
    sidebar_width = 400
    
    renderer = Renderer(screen, board_x, board_y, board_size)
    game_state = GameState()
    ui_manager = UIManager()
    
    difficulty = 'easy'
    
    ai_instances = {
        'easy': EasyAI(),
        'medium': MediumAI(),
        'hard': HardAI()
    }
    ai = ai_instances[difficulty]
    
    # 使用队列来传递AI的落子，避免线程安全问题
    ai_move_queue = queue.Queue()
    ai_thread = None
    is_game_over = False
    
    show_hints = False
    show_influence = False
    best_moves = []
    influence_map = []
    placed_times = {}
    
    difficulty_buttons = []
    current_difficulty_buttons = []
    
    # 按钮引用
    pass_btn = None
    undo_btn = None
    hints_btn = None
    
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
    
    def ai_worker():
        """AI工作线程"""
        try:
            # 检查是否轮到白棋且游戏在进行中
            if game_state.current_player == 'W' and game_state.game_status == 'playing':
                move = ai.get_move(game_state.board, game_state.current_player, game_state.rules, game_state.ko_point)
                if move is not None:
                    ai_move_queue.put(move)
                else:
                    # AI没有有效落子，发送PASS
                    game_state.pass_move()
                    ai_move_queue.put(None)
        except Exception as e:
            print(f"AI错误: {e}")
            import traceback
            traceback.print_exc()
            ai_move_queue.put(None)
    
    def start_ai_thinking():
        """启动AI思考"""
        nonlocal ai_thread
        if ai_thread is None or not ai_thread.is_alive():
            ai_thread = threading.Thread(target=ai_worker)
            ai_thread.daemon = True
            ai_thread.start()
    
    def undo_move():
        if game_state.game_status == 'playing' and not ai_thread:
            if len(game_state.history) >= 2:
                game_state.undo()
                game_state.undo()

    def end_game_func():
        if game_state.game_status == 'playing':
            game_state.end_game()

    def restart_game():
        nonlocal ai_thread, is_game_over, best_moves, influence_map, placed_times, difficulty
        ai_thread = None
        is_game_over = False
        best_moves = []
        influence_map = []
        placed_times = {}
        game_state.reset()
    
    def pass_move_func():
        if game_state.game_status == 'playing' and not ai_thread:
            if game_state.current_player == 'B':
                game_state.pass_move()
    
    def save_game_func():
        game_state.save_game()
    
    def load_game_func():
        nonlocal ai_thread, placed_times
        ai_thread = None
        placed_times = {}
        if game_state.load_game():
            pass
    
    def update_hints():
        nonlocal best_moves
        try:
            if game_state.game_status == 'playing' and game_state.current_player == 'B':
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
    
    # 创建按钮
    button_y = 40
    
    # 第一行：难度选择（游戏开始时设置，之后锁定）
    easy_btn = DifficultyButton(sidebar_x, button_y, 120, 38, "初级", set_difficulty_easy, 'easy', is_selected=True)
    ui_manager.add_component(easy_btn)
    difficulty_buttons.append(easy_btn)
    current_difficulty_buttons.append(easy_btn)
    
    medium_btn = DifficultyButton(sidebar_x + 130, button_y, 120, 38, "中级", set_difficulty_medium, 'medium')
    ui_manager.add_component(medium_btn)
    difficulty_buttons.append(medium_btn)
    current_difficulty_buttons.append(medium_btn)
    
    hard_btn = DifficultyButton(sidebar_x + 260, button_y, 120, 38, "高级", set_difficulty_hard, 'hard')
    ui_manager.add_component(hard_btn)
    difficulty_buttons.append(hard_btn)
    current_difficulty_buttons.append(hard_btn)
    
    # 第二行：PASS和悔棋
    button_y += 55
    pass_btn = Button(sidebar_x, button_y, 185, 38, "PASS", pass_move_func)
    ui_manager.add_component(pass_btn)
    
    undo_btn = Button(sidebar_x + 195, button_y, 185, 38, "悔棋", undo_move)
    ui_manager.add_component(undo_btn)
    
    # 第三行：提示和势力
    button_y += 55
    hints_btn = ToggleButton(sidebar_x, button_y, 185, 38, "提示: 关", "提示: 开", toggle_hints, is_on=False)
    ui_manager.add_component(hints_btn)
    
    influence_btn = ToggleButton(sidebar_x + 195, button_y, 185, 38, "势力: 关", "势力: 开", toggle_influence, is_on=False)
    ui_manager.add_component(influence_btn)
    
    # 第四行：保存和读取
    button_y += 55
    save_btn = Button(sidebar_x, button_y, 185, 38, "保存", save_game_func)
    ui_manager.add_component(save_btn)
    
    load_btn = Button(sidebar_x + 195, button_y, 185, 38, "读取", load_game_func)
    ui_manager.add_component(load_btn)
    
    # 第五行：结束游戏和重新开始
    button_y += 55
    end_game_btn = Button(sidebar_x, button_y, 185, 38, "结束游戏", end_game_func)
    ui_manager.add_component(end_game_btn)
    
    restart_btn = Button(sidebar_x + 195, button_y, 185, 38, "重新开始", restart_game)
    ui_manager.add_component(restart_btn)
    
    game_state_panel_y = button_y + 55
    
    def update_button_states():
        """更新按钮状态"""
        ai_busy = ai_thread is not None and ai_thread.is_alive()
        can_player_act = (game_state.game_status == 'playing' and 
                         not ai_busy and 
                         game_state.current_player == 'B')
        
        # PASS按钮：仅在玩家回合可用
        if pass_btn:
            pass_btn.active = can_player_act
            pass_btn.color = (40, 40, 50) if can_player_act else (25, 25, 35)
        
        # 悔棋按钮：玩家回合且有历史
        if undo_btn:
            can_undo = (game_state.game_status == 'playing' and 
                       not ai_busy and 
                       len(game_state.history) >= 2)
            undo_btn.active = can_undo
            undo_btn.color = (40, 40, 50) if can_undo else (25, 25, 35)
        
        # 难度选择：游戏进行中且无AI时可用（用于开局前选择）
        for btn in difficulty_buttons:
            btn.active = not ai_busy and game_state.game_status == 'playing'
    
    clock = pygame.time.Clock()
    running = True
    
    last_hint_update = 0
    hint_update_interval = 1.0
    
    print("围棋游戏启动！")
    print("选择难度后，点击棋盘下棋")
    
    while running:
        dt = clock.tick(60) / 1000.0
        events = []
        
        for event in pygame.event.get():
            events.append(event)
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    board_pos = renderer.screen_to_board(event.pos)
                    if board_pos is not None:
                        ai_busy = ai_thread is not None and ai_thread.is_alive()
                        if (game_state.current_player == 'B' and 
                            game_state.game_status == 'playing' and 
                            not ai_busy):
                            x, y = board_pos
                            if game_state.make_move(x, y):
                                placed_times[(x, y)] = renderer.animation_time
                                screen_pos = renderer.board_to_screen(x, y)
                                if screen_pos:
                                    renderer.add_place_particle(screen_pos[0], screen_pos[1], (255, 220, 150))
                                if show_hints:
                                    best_moves = []
                                if show_influence:
                                    update_influence()
        
        # 检测AI是否完成
        ai_busy = ai_thread is not None and ai_thread.is_alive()
        
        # 如果轮到白棋且AI没有在思考，启动AI
        if (not ai_busy and 
            game_state.current_player == 'W' and 
            game_state.game_status == 'playing' and
            ai_move_queue.empty()):
            start_ai_thinking()
        
        # 检查AI是否完成并处理落子 - 只处理一个移动
        if not ai_busy and not ai_move_queue.empty():
            try:
                move = ai_move_queue.get_nowait()
                if move is not None:
                    x, y = move
                    if game_state.make_move(x, y):
                        placed_times[(x, y)] = renderer.animation_time
                        screen_pos = renderer.board_to_screen(x, y)
                        if screen_pos:
                            renderer.add_place_particle(screen_pos[0], screen_pos[1], (200, 200, 220))
                    if show_hints:
                        best_moves = []
                    if show_influence:
                        update_influence()
                ai_thread = None
            except queue.Empty:
                pass
        
        # 更新提示
        current_time = time.time()
        ai_busy = ai_thread is not None and ai_thread.is_alive()
        if (show_hints and 
            game_state.game_status == 'playing' and 
            game_state.current_player == 'B' and 
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
        
        if show_influence and influence_map:
            renderer.draw_influence_map(screen, influence_map)
        
        renderer.draw_star_points(screen)
        
        ai_busy = ai_thread is not None and ai_thread.is_alive()
        if (show_hints and 
            best_moves and 
            game_state.current_player == 'B' and 
            game_state.game_status == 'playing' and 
            not ai_busy):
            renderer.draw_hints(screen, best_moves)
        
        renderer.draw_pieces(screen, game_state.board, placed_times)
        ui_manager.draw(screen)
        
        renderer.draw_current_player(screen, game_state.current_player, game_state.move_count, 
                                     game_state.captures, game_state.game_status, 
                                     game_state.winner, game_state.final_score, 
                                     info_y=game_state_panel_y)
        
        if ai_busy:
            renderer.draw_ai_thinking(screen, sidebar_x, game_state_panel_y + 210, 260)
        
        if game_state.game_status == 'playing':
            situation = game_state.estimate_situation()
            renderer.draw_situation_eval(screen, situation['win_rate'], situation['territory'], sidebar_x + 5, game_state_panel_y + 230)
        
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
