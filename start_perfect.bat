@echo off
REM MiMo 完美方案 - 启动脚本

cd /d "%~dp0"

echo ============================================
echo MiMo 完美方案
echo ============================================
echo 目标: 38B tokens
echo 任务: 50+ 高质量项目
echo 并发: 16 Agent
echo.
echo 按 Ctrl+C 停止
echo ============================================

python mimo_perfect.py

pause
