#!/usr/bin/env python3
"""
Skill Downloader - 从GitHub直接下载技能
安全第一原则：只下载官方仓库的技能
"""

import os
import json
import urllib.request
import zipfile
import io
import shutil
from pathlib import Path

# 配置
SKILLS_DIR = Path.home() / ".openclaw" / "skills"
TEMP_DIR = Path.home() / ".openclaw" / "temp_skills"

# 官方仓库列表 (S级安全)
OFFICIAL_REPOS = {
    "anthropics/skills": {
        "name": "Anthropic Skills",
        "stars": 146100,
        "security": "S",
        "skills": ["frontend-design", "skill-creator", "pdf", "docx", "xlsx", "pptx", "webapp-testing", "canvas-design"]
    },
    "mattpocock/skills": {
        "name": "Matt Pocock Skills",
        "stars": 116800,
        "security": "S",
        "skills": ["improve-codebase-architecture", "tdd", "diagnose", "to-prd", "to-issues", "handoff", "grill-me", "grill-with-docs", "prototype", "caveman", "triage", "zoom-out", "write-a-skill", "setup-matt-pocock-skills"]
    },
    "obra/superpowers": {
        "name": "Obra Superpowers",
        "stars": 216900,
        "security": "S",
        "skills": ["brainstorming", "systematic-debugging", "writing-plans", "executing-plans", "test-driven-development", "requesting-code-review", "receiving-code-review", "writing-skills", "dispatching-parallel-agents", "using-git-worktrees", "finishing-a-development-branch", "subagent-driven-development", "verification-before-completion", "using-superpowers"]
    },
    "vercel-labs/skills": {
        "name": "Vercel Skills",
        "stars": 50000,
        "security": "S",
        "skills": ["find-skills"]
    },
    "vercel-labs/agent-browser": {
        "name": "Vercel Agent Browser",
        "stars": 30000,
        "security": "S",
        "skills": ["agent-browser"]
    },
    "vercel-labs/agent-skills": {
        "name": "Vercel Agent Skills",
        "stars": 40000,
        "security": "S",
        "skills": ["vercel-react-best-practices", "web-design-guidelines", "vercel-composition-patterns", "vercel-react-native-skills"]
    },
    "coreyhaines31/marketingskills": {
        "name": "Corey Haines Marketing",
        "stars": 31800,
        "security": "S",
        "skills": ["copywriting", "seo-audit", "content-strategy", "marketing-psychology", "social-content", "programmatic-seo", "marketing-ideas", "copy-editing"]
    },
    "browser-use/browser-use": {
        "name": "Browser Use",
        "stars": 97100,
        "security": "A",
        "skills": ["browser-use"]
    },
    "scrapegraphai/just-scrape": {
        "name": "ScrapeGraphAI",
        "stars": 20000,
        "security": "A",
        "skills": ["just-scrape"]
    },
    "pbakaus/impeccable": {
        "name": "Impeccable",
        "stars": 15000,
        "security": "A",
        "skills": ["polish", "critique", "audit", "animate", "adapt", "clarify", "optimize", "colorize", "quieter", "impeccable"]
    },
    "supabase/agent-skills": {
        "name": "Supabase Skills",
        "stars": 25000,
        "security": "S",
        "skills": ["supabase-postgres-best-practices", "supabase"]
    },
    "firebase/agent-skills": {
        "name": "Firebase Skills",
        "stars": 20000,
        "security": "S",
        "skills": ["firebase-basics", "firebase-auth-basics"]
    }
}

def download_skill(repo, skill_name):
    """从GitHub下载技能"""
    print(f"📥 下载 {repo}/{skill_name}...")
    
    # 构建下载URL
    url = f"https://github.com/{repo}/archive/refs/heads/main.zip"
    
    try:
        # 下载仓库
        req = urllib.request.Request(url, headers={'User-Agent': 'ClawX-SkillDownloader/1.0'})
        with urllib.request.urlopen(req, timeout=30) as response:
            zip_data = response.read()
        
        # 解压到临时目录
        temp_skill_dir = TEMP_DIR / f"{repo.replace('/', '_')}_{skill_name}"
        if temp_skill_dir.exists():
            shutil.rmtree(temp_skill_dir)
        
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zip_ref:
            # 只解压技能目录
            for file_info in zip_ref.infolist():
                if file_info.filename.startswith(f"*/skills/{skill_name}/"):
                    # 提取文件
                    file_info.filename = file_info.filename.split(f"skills/{skill_name}/", 1)[1]
                    if file_info.filename:
                        zip_ref.extract(file_info, temp_skill_dir)
        
        # 复制到技能目录
        skill_dir = SKILLS_DIR / skill_name
        if skill_dir.exists():
            shutil.rmtree(skill_dir)
        
        if temp_skill_dir.exists():
            # 找到解压的目录
            extracted_dirs = list(temp_skill_dir.iterdir())
            if extracted_dirs:
                skills_subdir = extracted_dirs[0] / "skills" / skill_name
                if skills_subdir.exists():
                    shutil.copytree(skills_subdir, skill_dir)
                    print(f"✅ 安装成功: {skill_name}")
                    return True
                else:
                    # 尝试直接复制
                    shutil.copytree(extracted_dirs[0], skill_dir)
                    print(f"✅ 安装成功: {skill_name}")
                    return True
        
        print(f"⚠️ 技能目录未找到: {skill_name}")
        return False
        
    except Exception as e:
        print(f"❌ 下载失败 {skill_name}: {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始批量安装技能...")
    print(f"📁 技能目录: {SKILLS_DIR}")
    print()
    
    # 创建目录
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    
    # 统计
    total = 0
    success = 0
    failed = 0
    
    # 遍历官方仓库
    for repo, info in OFFICIAL_REPOS.items():
        print(f"\n📦 仓库: {info['name']} ({repo})")
        print(f"   ⭐ Stars: {info['stars']:,}")
        print(f"   🔒 安全等级: {info['security']}")
        
        for skill_name in info['skills']:
            total += 1
            if download_skill(repo, skill_name):
                success += 1
            else:
                failed += 1
    
    # 清理临时目录
    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)
    
    # 统计结果
    print("\n" + "=" * 50)
    print(f"📊 安装统计:")
    print(f"   总计: {total}")
    print(f"   成功: {success}")
    print(f"   失败: {failed}")
    print(f"   成功率: {success/total*100:.1f}%")

if __name__ == "__main__":
    main()
