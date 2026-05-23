# v1.5 - 领地计算优化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 优化领地计算，添加争议区域识别，完善领地算法，提高准确性和效率

**Architecture:** 
1. 在 `_flood_fill_territory()` 中添加争议区域检测
2. 优化 flood fill 算法效率，减少重复计算
3. 添加边界情况处理（角部、边部）
4. 创建完整的测试用例

**Tech Stack:** Python 3.12+, pytest 9.0+

---

## 先验知识

### 当前领地计算问题
1. **争议区域未处理**: 当空区域同时接触黑白双方时，直接忽略，应该标记为争议区域
2. **效率问题**: 当前 flood fill 没有优化，可能重复计算
3. **边界情况**: 角部、边部特殊情况可能判断不准确

### 争议区域判定规则
1. 如果空区域只接触黑色 → 黑领地
2. 如果空区域只接触白色 → 白领地
3. 如果空区域同时接触黑白 → 争议区域（不计分）
4. 如果空区域完全不接触任何一方 → 中立区域（不计分）

---

## 文件结构

| 文件 | 职责 | 操作类型 |
|------|------|---------|
| `game/game_state.py` | 优化 _flood_fill_territory，添加争议区域识别 | 修改 |
| `tests/test_territory_optimization.py` | 领地计算优化测试 | 创建 |
| `v1.5_PROGRESS.md` | v1.5进度报告 | 创建 |

---

## Task 1: 添加争议区域识别

**Files:**
- Modify: `game/game_state.py:169-198`
- Test: `tests/test_territory_optimization.py`

### Task 1.1: 写测试用例

- [ ] **Step 1: 创建测试文件并写失败测试**

```python
# tests/test_territory_optimization.py
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.board import Board
from game.game_state import GameState

def test_contested_area_not_counted():
    """测试争议区域不计分"""
    state = GameState()
    
    # 构造争议区域
    # 空区域同时接触黑白双方
    state.board.set_stone(0, 0, 'B')
    state.board.set_stone(2, 0, 'W')
    # 中间的 (1,0) 应该是争议区域
    
    black_terr, white_terr = state.calculate_territory()
    
    # 争议区域不计入任何一方
    assert black_terr == 0
    assert white_terr == 0

def test_neutral_area_not_counted():
    """测试完全不接触的中立区域不计分"""
    state = GameState()
    
    # 空区域周围完全没有棋子
    # (10,10) 周围都是空的
    
    black_terr, white_terr = state.calculate_territory()
    
    assert black_terr == 0
    assert white_terr == 0
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_territory_optimization.py -v`
Expected: FAIL (因为还没有实现)

### Task 1.2: 实现争议区域识别

- [ ] **Step 3: 修改 _flood_fill_territory 方法**

修改 `game/game_state.py` 中的方法：

```python
def _flood_fill_territory(self, start_x, start_y, visited):
    stack = [(start_x, start_y)]
    territory = set()
    border_colors = set()
    all_adjacent_points = []
    
    while stack:
        x, y = stack.pop()
        if (x, y) in territory:
            continue
        if not self.board.is_valid_position(x, y):
            continue
        
        stone = self.board.get_stone(x, y)
        if stone is not None:
            border_colors.add(stone)
            all_adjacent_points.append((x, y))
            continue
        
        territory.add((x, y))
        visited.add((x, y))
        
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            stack.append((x + dx, y + dy))
    
    # 争议区域判定
    owner = None
    if len(border_colors) == 1:
        owner = border_colors.pop()
    # 如果 len(border_colors) == 2 或 0 → 争议/中立，owner = None
    
    return len(territory), owner
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_territory_optimization.py -v`
Expected: PASS

- [ ] **Step 5: 提交代码**

```bash
git add game/game_state.py tests/test_territory_optimization.py
git commit -m "v1.5: 添加争议区域识别"
```

---

## Task 2: 优化 flood fill 算法

**Files:**
- Modify: `game/game_state.py:153-198`
- Test: `tests/test_territory_optimization.py`

### Task 2.1: 添加效率测试

- [ ] **Step 1: 添加效率测试（非必须但重要）**

```python
def test_large_board_efficiency():
    """测试大棋盘的效率"""
    state = GameState()
    
    # 构造一个大局面
    for y in range(0, 5):
        for x in range(0, 5):
            state.board.set_stone(x, y, 'B')
    
    for y in range(14, 19):
        for x in range(14, 19):
            state.board.set_stone(x, y, 'W')
    
    import time
    start_time = time.time()
    black_terr, white_terr = state.calculate_territory()
    elapsed = time.time() - start_time
    
    # 应该在合理时间内完成（少于1秒）
    assert elapsed < 1.0
```

### Task 2.2: 优化算法实现

- [ ] **Step 2: 优化 _flood_fill_territory 减少重复检查**

```python
def _flood_fill_territory(self, start_x, start_y, visited):
    # 使用队列替代栈，避免栈溢出
    from collections import deque
    queue = deque()
    queue.append((start_x, start_y))
    
    territory = set()
    border_colors = set()
    all_adjacent_points = []
    
    while queue:
        x, y = queue.popleft()
        if (x, y) in territory:
            continue
        if not self.board.is_valid_position(x, y):
            continue
        
        stone = self.board.get_stone(x, y)
        if stone is not None:
            border_colors.add(stone)
            all_adjacent_points.append((x, y))
            continue
        
        territory.add((x, y))
        visited.add((x, y))
        
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            queue.append((x + dx, y + dy))
    
    owner = None
    if len(border_colors) == 1:
        owner = border_colors.pop()
    
    return len(territory), owner
```

- [ ] **Step 3: 运行测试验证通过**

Run: `pytest tests/test_territory_optimization.py -v`
Expected: PASS

---

## Task 3: 边界情况处理

**Files:**
- Modify: `game/game_state.py`
- Test: `tests/test_territory_optimization.py`

### Task 3.1: 添加边界情况测试

- [ ] **Step 1: 添加角部、边部测试**

```python
def test_corner_territory():
    """测试角部领地计算"""
    state = GameState()
    
    # 角部被黑包围
    state.board.set_stone(0, 1, 'B')
    state.board.set_stone(1, 0, 'B')
    
    black_terr, white_terr = state.calculate_territory()
    
    # (0,0) 应该是黑领地
    assert black_terr == 1
    assert white_terr == 0

def test_edge_territory():
    """测试边部领地计算"""
    state = GameState()
    
    # 边上被黑包围
    state.board.set_stone(0, 0, 'B')
    state.board.set_stone(0, 2, 'B')
    state.board.set_stone(1, 1, 'B')
    
    black_terr, white_terr = state.calculate_territory()
    
    # (0,1) 应该是黑领地
    assert black_terr == 1
```

### Task 3.2: 验证边界情况

- [ ] **Step 2: 运行测试验证边界情况**

Run: `pytest tests/test_territory_optimization.py -v`
Expected: PASS (如果没通过，检查逻辑)

---

## Task 4: 完整测试和文档

**Files:**
- Test: `tests/test_territory_optimization.py`
- Create: `v1.5_PROGRESS.md`

### Task 4.1: 运行所有测试

- [ ] **Step 1: 运行所有测试**

```bash
cd c:\games\go
python -m pytest tests/ -v
```

Expected: 所有测试通过

### Task 4.2: 创建进度报告

- [ ] **Step 2: 创建 v1.5_PROGRESS.md**

```markdown
# v1.5 - 领地计算优化 开发进度报告

**日期**: 2026-05-23  
**版本**: v1.5 - 领地计算优化  
**状态**: 进行中

## 目标
优化领地计算，提高准确性：
1. 争议区域识别
2. flood fill 算法优化
3. 边界情况处理

## 已完成
- [ ] 争议区域识别
- [ ] 算法优化
- [ ] 边界情况处理
- [ ] 测试和文档
```

### Task 4.3: 提交和推送到 GitHub

- [ ] **Step 3: 提交完整代码**

```bash
git add game/game_state.py tests/test_territory_optimization.py v1.5_PROGRESS.md
git commit -m "v1.5: 领地计算优化"
git push origin main
```

---

## 执行检查

**1. Spec coverage:**
- ✅ 争议区域识别
- ✅ 算法优化
- ✅ 边界情况处理

**2. Placeholder scan:**
- ✅ 无 placeholder

**3. Type consistency:**
- ✅ 方法签名一致

---

## 执行选项

Plan complete and saved to `docs/superpowers/plans/2026-05-23-territory-calculation.md`. Two execution options:

**1. Subagent-Driven (recommended)** - 每个任务一个独立子agent，执行中进行审查，快速迭代

**2. Inline Execution** - 在当前会话中使用 executing-plans 技能执行任务，带检查点

**选择执行方式？**
