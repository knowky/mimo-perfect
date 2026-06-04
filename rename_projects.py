#!/usr/bin/env python3
"""整理项目目录 - 使用中文名称"""

import json
import os
import sys
import shutil
from pathlib import Path

# 设置控制台编码
sys.stdout.reconfigure(encoding='utf-8')

PROJECTS_DIR = Path(__file__).parent / "projects"
TASKS_FILE = Path(__file__).parent / "tasks.json"

# 加载任务定义
with open(TASKS_FILE, "r", encoding="utf-8") as f:
    tasks = json.load(f)

# 创建 ID -> 标题映射
task_map = {}
for task in tasks:
    task_id = task["id"]
    title = task["title"]
    # 清理标题，用作目录名
    safe_title = "".join(c for c in title if c.isalnum() or c in "._- ").strip()
    # 截断过长的标题
    if len(safe_title) > 30:
        safe_title = safe_title[:30].strip()
    task_map[task_id] = safe_title

print("任务映射表:")
print("=" * 60)

# 遍历项目目录
for project_dir in sorted(PROJECTS_DIR.iterdir()):
    if not project_dir.is_dir():
        continue
    
    old_name = project_dir.name
    if old_name in task_map:
        new_name = task_map[old_name]
        print(f"  {old_name:20s} -> {new_name}")
    else:
        print(f"  {old_name:20s} -> (未找到映射)")

print("\n" + "=" * 60)
print("开始重命名...")

# 执行重命名
renamed = 0
for project_dir in sorted(PROJECTS_DIR.iterdir()):
    if not project_dir.is_dir():
        continue
    
    old_name = project_dir.name
    if old_name in task_map:
        new_name = task_map[old_name]
        new_path = project_dir.parent / new_name
        
        if project_dir != new_path and not new_path.exists():
            os.rename(project_dir, new_path)
            print(f"  ✓ {old_name} -> {new_name}")
            renamed += 1
        elif new_path.exists():
            print(f"  ⚠ {new_name} 已存在，跳过")
        else:
            print(f"  - {old_name} 无需重命名")

print(f"\n完成! 重命名 {renamed} 个目录")
