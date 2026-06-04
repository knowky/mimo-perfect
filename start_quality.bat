@echo off
REM MiMo 高质量内容生产 - 启动脚本

cd /d "%~dp0"

echo ============================================
echo MiMo 高质量内容生产系统
echo ============================================
echo 目标: 38B tokens, 6天
echo 并发: 100
echo 质量迭代: 3 轮
echo.
echo 按 Ctrl+C 停止
echo ============================================

python mimo_quality.py

pause
