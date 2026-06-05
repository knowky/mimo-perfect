#!/usr/bin/env python3
"""清理旧项目，合并成1-2个核心文件"""

import os
from pathlib import Path

PROJECTS_DIR = Path(__file__).parent / "projects"

def merge_project(project_dir):
    """合并项目中的多个文件为一个完整报告"""
    md_files = list(project_dir.glob("*.md"))
    
    # 跳过已经有 完整报告.md 的项目
    if any(f.name == "完整报告.md" for f in md_files):
        print(f"跳过 {project_dir.name} (已有完整报告.md)")
        return
    
    # 读取所有文件内容
    contents = []
    for f in md_files:
        if f.name != "README.md":
            try:
                with open(f, "r", encoding="utf-8") as file:
                    contents.append({"name": f.name, "content": file.read()})
            except Exception as e:
                print(f"读取 {f.name} 失败: {e}")
    
    if not contents:
        print(f"跳过 {project_dir.name} (没有内容文件)")
        return
    
    # 生成完整报告
    report_content = f"# {project_dir.name}\n\n"
    report_content += f"**生成时间**: 2026-06-05\n\n---\n\n"
    
    for item in contents:
        report_content += f"## {item['name']}\n\n{item['content']}\n\n---\n\n"
    
    # 保存完整报告
    report_file = project_dir / "完整报告.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_content)
    
    # 更新 README
    readme_content = f"# {project_dir.name}\n\n"
    readme_content += f"## 项目信息\n- **目录**: {project_dir.name}\n- **文件数**: {len(contents)} 个子任务\n\n"
    readme_content += f"## 输出文件\n- [完整报告.md](完整报告.md)\n\n"
    readme_content += f"## 生成时间\n2026-06-05\n"
    
    readme_file = project_dir / "README.md"
    with open(readme_file, "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    # 删除旧文件（保留 README.md 和 完整报告.md）
    for f in md_files:
        if f.name not in ["README.md", "完整报告.md"]:
            try:
                f.unlink()
                print(f"删除 {f.name}")
            except Exception as e:
                print(f"删除 {f.name} 失败: {e}")
    
    print(f"完成 {project_dir.name}: {len(contents)} 个文件合并为完整报告.md")

def main():
    print("开始清理项目目录...")
    
    for project_dir in PROJECTS_DIR.iterdir():
        if project_dir.is_dir():
            merge_project(project_dir)
    
    print("\n清理完成！")

if __name__ == "__main__":
    main()
