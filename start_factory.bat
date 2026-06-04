@echo off
REM MiMo Content Factory - Windows 启动脚本

cd /d "%~dp0"

echo ============================================
echo MiMo Content Factory
echo ============================================
echo 目标: 38B tokens, 6天
echo 并发: 50
echo 输出: output/
echo.
echo 按 Ctrl+C 停止
echo ============================================

python mimo_factory.py

pause
