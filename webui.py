#!/usr/bin/env python3
"""MiMo 项目 Web UI - 现代化设计"""

import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import unquote
import webbrowser
from datetime import datetime, timedelta

PROJECTS_DIR = Path(__file__).parent / "projects"
STATS_FILE = Path(__file__).parent / "perfect_stats.json"
TASKS_FILE = Path(__file__).parent / "tasks.json"
PORT = 8888

def load_tasks():
    try:
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def get_stats():
    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"total_tokens": 0, "total_calls": 0, "completed_tasks": 0, "failed_tasks": 0}

def get_project_progress():
    stats = get_stats()
    tasks = load_tasks()
    
    task_counts = {}
    for h in stats.get("task_history", []):
        tid = h.get("task_id", "")
        if tid not in task_counts:
            task_counts[tid] = 0
        task_counts[tid] += 1
    
    projects = []
    for task in tasks:
        tid = task["id"]
        title = task["title"]
        expected = task.get("expected_tokens", 100000000)
        subtasks = task.get("tasks", [])
        num_subtasks = len(subtasks) if subtasks else 1
        
        completed = task_counts.get(tid, 0)
        progress = min(100, (completed / num_subtasks) * 100) if num_subtasks > 0 else 0
        consumed = completed * 40000
        
        project_dir = PROJECTS_DIR / task.get("output_dir", "").replace("projects/", "")
        files = list(project_dir.glob("*.md")) if project_dir.exists() else []
        
        # 确定项目类型和图标
        task_type = task.get("type", "research")
        type_icons = {
            "research": "🔬",
            "code": "💻",
            "tutorial": "📚",
            "writing": "✍️",
            "analysis": "📊"
        }
        
        projects.append({
            "id": tid,
            "title": title,
            "type": task_type,
            "icon": type_icons.get(task_type, "📁"),
            "expected": expected,
            "consumed": consumed,
            "completed": completed,
            "total_subtasks": num_subtasks,
            "progress": progress,
            "files": len(files),
            "size": sum(f.stat().st_size for f in files) / 1024 if files else 0,
            "subtasks": subtasks
        })
    
    return projects

def get_overall_progress():
    stats = get_stats()
    total_tokens = stats.get("total_tokens", 0)
    target = 38000000000
    
    start_time = stats.get("start_time")
    if start_time:
        start = datetime.fromisoformat(start_time)
        now = datetime.now()
        hours = (now - start).total_seconds() / 3600
        rate = total_tokens / hours if hours > 0 else 0
    else:
        rate = 0
    
    remaining = target - total_tokens
    if rate > 0:
        hours_left = remaining / rate
        eta = datetime.now() + timedelta(hours=hours_left)
    else:
        hours_left = 0
        eta = None
    
    return {
        "total_tokens": total_tokens,
        "target": target,
        "progress": (total_tokens / target) * 100,
        "rate": rate,
        "hours_left": hours_left,
        "eta": eta
    }

class MiMoHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        path = unquote(self.path)
        
        if path == "/" or path == "/index.html":
            self.send_html(self.index_page())
        elif path == "/api/stats":
            self.send_json(get_stats())
        elif path == "/api/projects":
            self.send_json(get_project_progress())
        elif path == "/api/progress":
            self.send_json(get_overall_progress())
        elif path.startswith("/project/"):
            project_id = path.split("/project/")[1]
            self.send_html(self.project_detail_page(project_id))
        elif path.startswith("/file/"):
            parts = path.split("/")
            if len(parts) >= 3:
                project_name = parts[2]
                file_name = "/".join(parts[3:])
                content = read_file(project_name, file_name)
                self.send_html(self.file_page(project_name, file_name, content))
            else:
                self.send_error(404)
        else:
            self.send_error(404)
    
    def send_html(self, html):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))
    
    def send_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
    
    def index_page(self):
        stats = get_stats()
        projects = get_project_progress()
        progress = get_overall_progress()
        
        # 按类型分组
        projects_by_type = {}
        for p in projects:
            t = p['type']
            if t not in projects_by_type:
                projects_by_type[t] = []
            projects_by_type[t].append(p)
        
        # 统计每种类型的进度
        type_stats = []
        type_names = {
            "research": "研究报告",
            "code": "代码项目", 
            "tutorial": "技术教程",
            "writing": "科幻小说",
            "analysis": "行业分析"
        }
        type_icons = {
            "research": "🔬",
            "code": "💻",
            "tutorial": "📚",
            "writing": "✍️",
            "analysis": "📊"
        }
        
        for t, name in type_names.items():
            ps = projects_by_type.get(t, [])
            if ps:
                avg_progress = sum(p['progress'] for p in ps) / len(ps)
                total_completed = sum(p['completed'] for p in ps)
                total_subtasks = sum(p['total_subtasks'] for p in ps)
                type_stats.append({
                    "type": t,
                    "name": name,
                    "icon": type_icons[t],
                    "count": len(ps),
                    "progress": avg_progress,
                    "completed": total_completed,
                    "subtasks": total_subtasks
                })
        
        # 项目卡片 HTML
        project_cards = ""
        for p in projects:
            color = "#10b981" if p['progress'] >= 80 else "#f59e0b" if p['progress'] >= 50 else "#3b82f6"
            status_class = "completed" if p['progress'] >= 100 else "active" if p['progress'] > 0 else "pending"
            
            project_cards += f'''
            <div class="project-card {status_class}" onclick="location.href='/project/{p['id']}'">
                <div class="card-glow"></div>
                <div class="card-content">
                    <div class="card-header">
                        <div class="card-icon">{p['icon']}</div>
                        <div class="card-badge">{p['id']}</div>
                    </div>
                    <h3 class="card-title">{p['title']}</h3>
                    <div class="card-progress">
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {p['progress']:.1f}%; background: {color};"></div>
                        </div>
                        <span class="progress-text">{p['progress']:.0f}%</span>
                    </div>
                    <div class="card-stats">
                        <div class="stat">
                            <span class="stat-icon">📝</span>
                            <span>{p['completed']}/{p['total_subtasks']}</span>
                        </div>
                        <div class="stat">
                            <span class="stat-icon">📄</span>
                            <span>{p['files']} 文件</span>
                        </div>
                        <div class="stat">
                            <span class="stat-icon">💾</span>
                            <span>{p['size']:.0f} KB</span>
                        </div>
                    </div>
                </div>
            </div>
            '''
        
        # 类型统计卡片
        type_cards = ""
        for ts in type_stats:
            type_cards += f'''
            <div class="type-card">
                <div class="type-icon">{ts['icon']}</div>
                <div class="type-info">
                    <div class="type-name">{ts['name']}</div>
                    <div class="type-count">{ts['count']} 个项目</div>
                </div>
                <div class="type-progress">
                    <div class="progress-ring" data-progress="{ts['progress']:.0f}">
                        <svg viewBox="0 0 36 36">
                            <path class="ring-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"/>
                            <path class="ring-fill" stroke="{ '#10b981' if ts['progress'] >= 80 else '#f59e0b' if ts['progress'] >= 50 else '#3b82f6' }" 
                                  stroke-dasharray="{ts['progress']:.0f}, 100" 
                                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"/>
                        </svg>
                        <span class="ring-text">{ts['progress']:.0f}%</span>
                    </div>
                </div>
            </div>
            '''
        
        # 进度信息
        progress_color = "#10b981" if progress['progress'] >= 80 else "#f59e0b" if progress['progress'] >= 50 else "#3b82f6"
        time_left = f"{progress['hours_left']/24:.1f} 天" if progress['hours_left'] > 24 else f"{progress['hours_left']:.1f} 小时"
        eta_str = progress['eta'].strftime("%m-%d %H:%M") if progress['eta'] else "计算中"
        
        # 配置信息
        config_html = '''
        <div class="config-section">
            <div class="section-title">⚙️ 当前配置</div>
            <div class="config-grid">
                <div class="config-item">
                    <span class="config-icon">⚡</span>
                    <span class="config-label">并发数</span>
                    <span class="config-value">8</span>
                </div>
                <div class="config-item">
                    <span class="config-icon">📝</span>
                    <span class="config-label">每次输出</span>
                    <span class="config-value">16K tokens</span>
                </div>
                <div class="config-item">
                    <span class="config-icon">⏱️</span>
                    <span class="config-label">休息间隔</span>
                    <span class="config-value">2 秒</span>
                </div>
                <div class="config-item">
                    <span class="config-icon">🎯</span>
                    <span class="config-label">目标</span>
                    <span class="config-value">38B Credits</span>
                </div>
                <div class="config-item">
                    <span class="config-icon">📊</span>
                    <span class="config-label">预计速率</span>
                    <span class="config-value">~230M/小时</span>
                </div>
                <div class="config-item">
                    <span class="config-icon">⏰</span>
                    <span class="config-label">预计完成</span>
                    <span class="config-value">~7 天</span>
                </div>
            </div>
            <div class="config-note">💡 低优先级运行，不影响 ClawX 正常使用</div>
        </div>
        '''
        
        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MiMo Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-card: #1e293b;
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --accent: #3b82f6;
            --accent-light: #60a5fa;
            --success: #10b981;
            --warning: #f59e0b;
            --error: #ef4444;
            --border: #334155;
            --glow: rgba(59, 130, 246, 0.3);
        }}
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }}
        
        /* Header */
        .header {{
            text-align: center;
            margin-bottom: 3rem;
            padding: 2rem;
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(139, 92, 246, 0.1));
            border-radius: 20px;
            border: 1px solid var(--border);
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--accent-light), #8b5cf6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }}
        
        .header p {{
            color: var(--text-secondary);
            font-size: 1.1rem;
        }}
        
        /* Stats Grid */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 1rem;
            margin: 2rem 0;
        }}
        
        .stat-card {{
            background: var(--bg-card);
            padding: 1.5rem;
            border-radius: 16px;
            border: 1px solid var(--border);
            text-align: center;
            transition: all 0.3s ease;
        }}
        
        .stat-card:hover {{
            border-color: var(--accent);
            box-shadow: 0 0 20px var(--glow);
            transform: translateY(-2px);
        }}
        
        .stat-value {{
            font-size: 2rem;
            font-weight: 700;
            color: var(--accent-light);
            margin-bottom: 0.3rem;
        }}
        
        .stat-label {{
            font-size: 0.85rem;
            color: var(--text-secondary);
        }}
        
        /* Main Progress */
        .progress-section {{
            background: var(--bg-card);
            border-radius: 20px;
            padding: 2rem;
            margin: 2rem 0;
            border: 1px solid var(--border);
        }}
        
        .progress-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
        }}
        
        .progress-title {{
            font-size: 1.2rem;
            font-weight: 600;
        }}
        
        .progress-badge {{
            background: var(--accent);
            color: white;
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 500;
        }}
        
        .progress-bar-main {{
            height: 20px;
            background: var(--bg-primary);
            border-radius: 10px;
            overflow: hidden;
            margin: 1rem 0;
            position: relative;
        }}
        
        .progress-fill-main {{
            height: 100%;
            background: linear-gradient(90deg, var(--accent), var(--accent-light));
            border-radius: 10px;
            transition: width 1s ease;
            position: relative;
        }}
        
        .progress-fill-main::after {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.2) 50%, transparent 100%);
            animation: shimmer 2s infinite;
        }}
        
        @keyframes shimmer {{
            0% {{ transform: translateX(-100%); }}
            100% {{ transform: translateX(100%); }}
        }}
        
        .progress-info {{
            display: flex;
            justify-content: space-between;
            font-size: 0.9rem;
            color: var(--text-secondary);
            margin-top: 0.5rem;
        }}
        
        /* Type Cards */
        .type-section {{
            margin: 3rem 0;
        }}
        
        .section-title {{
            font-size: 1.3rem;
            font-weight: 600;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .type-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
        }}
        
        .type-card {{
            background: var(--bg-card);
            padding: 1.5rem;
            border-radius: 16px;
            border: 1px solid var(--border);
            display: flex;
            align-items: center;
            gap: 1rem;
            transition: all 0.3s ease;
        }}
        
        .type-card:hover {{
            border-color: var(--accent);
            transform: translateY(-2px);
        }}
        
        .type-icon {{
            font-size: 2rem;
            width: 50px;
            height: 50px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(59, 130, 246, 0.1);
            border-radius: 12px;
        }}
        
        .type-info {{
            flex: 1;
        }}
        
        .type-name {{
            font-weight: 600;
            margin-bottom: 0.2rem;
        }}
        
        .type-count {{
            font-size: 0.85rem;
            color: var(--text-secondary);
        }}
        
        .progress-ring {{
            position: relative;
            width: 60px;
            height: 60px;
        }}
        
        .progress-ring svg {{
            transform: rotate(-90deg);
        }}
        
        .ring-bg {{
            fill: none;
            stroke: var(--bg-primary);
            stroke-width: 3;
        }}
        
        .ring-fill {{
            fill: none;
            stroke-width: 3;
            stroke-linecap: round;
            transition: stroke-dasharray 0.5s ease;
        }}
        
        .ring-text {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 0.75rem;
            font-weight: 600;
        }}
        
        /* Project Grid */
        .projects-section {{
            margin: 3rem 0;
        }}
        
        .config-section {{
            background: var(--bg-card);
            border-radius: 20px;
            padding: 2rem;
            margin: 2rem 0;
            border: 1px solid var(--border);
        }}
        
        .config-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin: 1rem 0;
        }}
        
        .config-item {{
            background: var(--bg-primary);
            padding: 1rem;
            border-radius: 12px;
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 0.3rem;
        }}
        
        .config-icon {{
            font-size: 1.5rem;
        }}
        
        .config-label {{
            font-size: 0.8rem;
            color: var(--text-secondary);
        }}
        
        .config-value {{
            font-size: 1rem;
            font-weight: 600;
            color: var(--accent-light);
        }}
        
        .config-note {{
            margin-top: 1rem;
            padding: 0.8rem;
            background: rgba(16, 185, 129, 0.1);
            border-radius: 8px;
            text-align: center;
            font-size: 0.9rem;
            color: #10b981;
        }}
        
        .projects-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
        }}
        
        .filter-buttons {{
            display: flex;
            gap: 0.5rem;
        }}
        
        .filter-btn {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            color: var(--text-secondary);
            padding: 0.5rem 1rem;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.85rem;
            transition: all 0.2s ease;
        }}
        
        .filter-btn:hover, .filter-btn.active {{
            background: var(--accent);
            color: white;
            border-color: var(--accent);
        }}
        
        .projects-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 1.5rem;
        }}
        
        .project-card {{
            background: var(--bg-card);
            border-radius: 16px;
            border: 1px solid var(--border);
            overflow: hidden;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
        }}
        
        .project-card:hover {{
            border-color: var(--accent);
            box-shadow: 0 10px 40px var(--glow);
            transform: translateY(-5px);
        }}
        
        .card-glow {{
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, var(--accent), var(--accent-light));
            opacity: 0;
            transition: opacity 0.3s ease;
        }}
        
        .project-card:hover .card-glow {{
            opacity: 1;
        }}
        
        .project-card.completed {{
            border-color: var(--success);
        }}
        
        .project-card.completed .card-glow {{
            background: linear-gradient(90deg, var(--success), #34d399);
        }}
        
        .project-card.active {{
            border-color: var(--warning);
        }}
        
        .card-content {{
            padding: 1.5rem;
        }}
        
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }}
        
        .card-icon {{
            font-size: 1.5rem;
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(59, 130, 246, 0.1);
            border-radius: 10px;
        }}
        
        .card-badge {{
            font-size: 0.75rem;
            color: var(--text-secondary);
            background: var(--bg-primary);
            padding: 0.2rem 0.6rem;
            border-radius: 6px;
        }}
        
        .card-title {{
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 1rem;
            line-height: 1.4;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}
        
        .card-progress {{
            display: flex;
            align-items: center;
            gap: 0.8rem;
            margin-bottom: 1rem;
        }}
        
        .progress-bar {{
            flex: 1;
            height: 8px;
            background: var(--bg-primary);
            border-radius: 4px;
            overflow: hidden;
        }}
        
        .progress-fill {{
            height: 100%;
            border-radius: 4px;
            transition: width 0.5s ease;
        }}
        
        .progress-text {{
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text-secondary);
            min-width: 40px;
            text-align: right;
        }}
        
        .card-stats {{
            display: flex;
            justify-content: space-between;
            padding-top: 1rem;
            border-top: 1px solid var(--border);
        }}
        
        .stat {{
            display: flex;
            align-items: center;
            gap: 0.3rem;
            font-size: 0.8rem;
            color: var(--text-secondary);
        }}
        
        .stat-icon {{
            font-size: 0.9rem;
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            .container {{
                padding: 1rem;
            }}
            
            .header h1 {{
                font-size: 2rem;
            }}
            
            .stats-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
            
            .projects-grid {{
                grid-template-columns: 1fr;
            }}
        }}
        
        /* Animations */
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .project-card {{
            animation: fadeIn 0.5s ease forwards;
        }}
        
        .project-card:nth-child(1) {{ animation-delay: 0.05s; }}
        .project-card:nth-child(2) {{ animation-delay: 0.1s; }}
        .project-card:nth-child(3) {{ animation-delay: 0.15s; }}
        .project-card:nth-child(4) {{ animation-delay: 0.2s; }}
        .project-card:nth-child(5) {{ animation-delay: 0.25s; }}
        .project-card:nth-child(6) {{ animation-delay: 0.3s; }}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>🚀 MiMo Dashboard</h1>
            <p>AI 内容生成进度实时监控 | 目标: 38B Credits</p>
        </header>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{progress['total_tokens'] / 1e9:.2f}B</div>
                <div class="stat-label">已消耗 Credits</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['completed_tasks']}</div>
                <div class="stat-label">已完成任务</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['total_calls']}</div>
                <div class="stat-label">API 调用</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(projects)}</div>
                <div class="stat-label">项目总数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{progress['rate'] / 1e6:.0f}M</div>
                <div class="stat-label">速率/小时</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{time_left}</div>
                <div class="stat-label">预计剩余</div>
            </div>
        </div>
        
        <div class="progress-section">
            <div class="progress-header">
                <div class="progress-title">📊 总体进度</div>
                <div class="progress-badge">{progress['progress']:.2f}%</div>
            </div>
            <div class="progress-bar-main">
                <div class="progress-fill-main" style="width: {min(100, progress['progress']):.2f}%;"></div>
            </div>
            <div class="progress-info">
                <span>目标: {progress['target'] / 1e9:.0f}B Credits</span>
                <span>已用: {progress['total_tokens'] / 1e9:.2f}B</span>
                <span>预计完成: {eta_str}</span>
            </div>
        </div>
        
        {config_html}
        
        <div class="type-section">
            <div class="section-title">📁 项目分类</div>
            <div class="type-grid">
                {type_cards}
            </div>
        </div>
        
        <div class="projects-section">
            <div class="projects-header">
                <div class="section-title">📋 全部项目</div>
                <div class="filter-buttons">
                    <button class="filter-btn active" onclick="filterProjects('all')">全部</button>
                    <button class="filter-btn" onclick="filterProjects('active')">进行中</button>
                    <button class="filter-btn" onclick="filterProjects('completed')">已完成</button>
                    <button class="filter-btn" onclick="filterProjects('pending')">未开始</button>
                </div>
            </div>
            <div class="projects-grid" id="projectsGrid">
                {project_cards}
            </div>
        </div>
    </div>
    
    <script>
        function filterProjects(filter) {{
            // 更新按钮状态
            document.querySelectorAll('.filter-btn').forEach(btn => {{
                btn.classList.remove('active');
                if(btn.textContent.includes(filter === 'all' ? '全部' : 
                    filter === 'active' ? '进行中' : 
                    filter === 'completed' ? '已完成' : '未开始')) {{
                    btn.classList.add('active');
                }}
            }});
            
            // 筛选卡片
            document.querySelectorAll('.project-card').forEach(card => {{
                const progress = parseFloat(card.querySelector('.progress-text').textContent);
                switch(filter) {{
                    case 'active':
                        card.style.display = progress > 0 && progress < 100 ? 'block' : 'none';
                        break;
                    case 'completed':
                        card.style.display = progress >= 100 ? 'block' : 'none';
                        break;
                    case 'pending':
                        card.style.display = progress === 0 ? 'block' : 'none';
                        break;
                    default:
                        card.style.display = 'block';
                }}
            }});
        }}
        
        // 自动刷新
        setInterval(() => location.reload(), 60000);
    </script>
</body>
</html>'''
    
    def project_detail_page(self, project_id):
        projects = get_project_progress()
        project = next((p for p in projects if p['id'] == project_id), None)
        
        if not project:
            return "<h1>项目未找到</h1><a href='/'>返回</a>"
        
        subtasks_html = ""
        for i, task in enumerate(project['subtasks'], 1):
            completed = i <= project['completed']
            icon = "✅" if completed else "⏳"
            subtasks_html += f'''
            <div class="subtask-item {'completed' if completed else ''}">
                <span class="subtask-icon">{icon}</span>
                <span>{task}</span>
            </div>
            '''
        
        project_dir = PROJECTS_DIR / project_id
        files_html = ""
        if project_dir.exists():
            for f in sorted(project_dir.glob("*.md")):
                size_kb = f.stat().st_size / 1024
                files_html += f'''
                <div class="file-item" onclick="location.href='/file/{project_id}/{f.name}'">
                    <div class="file-info">
                        <span class="file-icon">📄</span>
                        <span class="file-name">{f.name}</span>
                    </div>
                    <span class="file-size">{size_kb:.1f} KB</span>
                </div>
                '''
        
        color = "#10b981" if project['progress'] >= 80 else "#f59e0b" if project['progress'] >= 50 else "#3b82f6"
        
        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project['title']} - MiMo</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-card: #1e293b;
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --accent: #3b82f6;
            --accent-light: #60a5fa;
            --success: #10b981;
            --warning: #f59e0b;
            --border: #334155;
        }}
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            padding: 2rem;
        }}
        
        .back-btn {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            color: var(--accent-light);
            text-decoration: none;
            font-weight: 500;
            margin-bottom: 2rem;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            transition: background 0.2s ease;
        }}
        
        .back-btn:hover {{
            background: rgba(59, 130, 246, 0.1);
        }}
        
        .detail-card {{
            background: var(--bg-card);
            border-radius: 20px;
            border: 1px solid var(--border);
            padding: 2rem;
            margin-bottom: 2rem;
        }}
        
        .detail-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            padding-bottom: 1.5rem;
            border-bottom: 2px solid var(--border);
        }}
        
        .detail-title {{
            font-size: 1.8rem;
            font-weight: 700;
        }}
        
        .detail-badge {{
            background: var(--accent);
            color: white;
            padding: 0.4rem 1rem;
            border-radius: 20px;
            font-size: 0.9rem;
        }}
        
        .progress-section {{
            margin: 2rem 0;
        }}
        
        .progress-bar {{
            height: 16px;
            background: var(--bg-primary);
            border-radius: 8px;
            overflow: hidden;
            margin: 1rem 0;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, var(--accent), var(--accent-light));
            border-radius: 8px;
            transition: width 0.5s ease;
        }}
        
        .progress-text {{
            text-align: center;
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--accent-light);
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin: 2rem 0;
        }}
        
        .stat-item {{
            background: var(--bg-primary);
            padding: 1.2rem;
            border-radius: 12px;
            text-align: center;
        }}
        
        .stat-value {{
            font-size: 1.8rem;
            font-weight: 700;
            color: var(--accent-light);
            margin-bottom: 0.3rem;
        }}
        
        .stat-label {{
            font-size: 0.85rem;
            color: var(--text-secondary);
        }}
        
        .section-title {{
            font-size: 1.2rem;
            font-weight: 600;
            margin: 2rem 0 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .subtask-list {{
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }}
        
        .subtask-item {{
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 1rem;
            background: var(--bg-primary);
            border-radius: 10px;
            transition: all 0.2s ease;
        }}
        
        .subtask-item:hover {{
            background: rgba(59, 130, 246, 0.1);
        }}
        
        .subtask-item.completed {{
            opacity: 0.7;
        }}
        
        .subtask-icon {{
            font-size: 1.2rem;
        }}
        
        .file-list {{
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }}
        
        .file-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem;
            background: var(--bg-primary);
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        
        .file-item:hover {{
            background: rgba(59, 130, 246, 0.1);
            transform: translateX(5px);
        }}
        
        .file-info {{
            display: flex;
            align-items: center;
            gap: 0.8rem;
        }}
        
        .file-icon {{
            font-size: 1.2rem;
        }}
        
        .file-name {{
            font-weight: 500;
        }}
        
        .file-size {{
            color: var(--text-secondary);
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <a class="back-btn" href="/">← 返回仪表盘</a>
        
        <div class="detail-card">
            <div class="detail-header">
                <h1 class="detail-title">{project['icon']} {project['title']}</h1>
                <span class="detail-badge">{project['id']}</span>
            </div>
            
            <div class="progress-section">
                <div class="progress-text">{project['progress']:.1f}%</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {project['progress']:.1f}%;"></div>
                </div>
            </div>
            
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value">{project['completed']}</div>
                    <div class="stat-label">已完成子任务</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{project['total_subtasks']}</div>
                    <div class="stat-label">总子任务数</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{project['files']}</div>
                    <div class="stat-label">生成文件</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{project['size']:.0f}</div>
                    <div class="stat-label">内容大小 (KB)</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{project['consumed'] / 1e6:.1f}M</div>
                    <div class="stat-label">已消耗 Tokens</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{project['expected'] / 1e6:.0f}M</div>
                    <div class="stat-label">目标 Tokens</div>
                </div>
            </div>
        </div>
        
        <div class="detail-card">
            <div class="section-title">📋 子任务列表</div>
            <div class="subtask-list">
                {subtasks_html}
            </div>
        </div>
        
        <div class="detail-card">
            <div class="section-title">📁 生成的文件</div>
            <div class="file-list">
                {files_html if files_html else '<p style="color: var(--text-secondary); padding: 1rem;">暂无文件</p>'}
            </div>
        </div>
    </div>
</body>
</html>'''
    
    def file_page(self, project_name, file_name, content):
        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{file_name} - MiMo</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-card: #1e293b;
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --accent: #3b82f6;
            --accent-light: #60a5fa;
            --border: #334155;
        }}
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 2rem;
        }}
        
        .breadcrumb {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 1.5rem;
            font-size: 0.9rem;
            color: var(--text-secondary);
        }}
        
        .breadcrumb a {{
            color: var(--accent-light);
            text-decoration: none;
        }}
        
        .breadcrumb a:hover {{
            text-decoration: underline;
        }}
        
        .back-btn {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            color: var(--accent-light);
            text-decoration: none;
            font-weight: 500;
            margin-bottom: 2rem;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            transition: background 0.2s ease;
        }}
        
        .back-btn:hover {{
            background: rgba(59, 130, 246, 0.1);
        }}
        
        .file-header {{
            margin-bottom: 2rem;
        }}
        
        .file-title {{
            font-size: 1.8rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }}
        
        .file-meta {{
            color: var(--text-secondary);
            font-size: 0.95rem;
        }}
        
        .content-card {{
            background: var(--bg-card);
            border-radius: 16px;
            border: 1px solid var(--border);
            padding: 2rem;
        }}
        
        .content-card pre {{
            white-space: pre-wrap;
            word-wrap: break-word;
            line-height: 1.8;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.95rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="breadcrumb">
            <a href="/">首页</a>
            <span>/</span>
            <a href="/project/{project_name}">{project_name}</a>
            <span>/</span>
            <span>{file_name}</span>
        </div>
        
        <a class="back-btn" href="/project/{project_name}">← 返回项目详情</a>
        
        <div class="file-header">
            <h1 class="file-title">{project_name}</h1>
            <div class="file-meta">📄 {file_name}</div>
        </div>
        
        <div class="content-card">
            <pre>{content}</pre>
        </div>
    </div>
</body>
</html>'''

def read_file(project_name, file_name):
    file_path = PROJECTS_DIR / project_name / file_name
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return "文件不存在"

if __name__ == "__main__":
    print(f"🚀 启动 MiMo Dashboard: http://localhost:{PORT}")
    print("按 Ctrl+C 停止")
    
    webbrowser.open(f"http://localhost:{PORT}")
    
    server = HTTPServer(("localhost", PORT), MiMoHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")
        server.shutdown()
