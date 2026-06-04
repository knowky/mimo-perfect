@echo off
REM MiMo Content Factory - 后台启动脚本

cd /d "%~dp0"

echo 启动 MiMo Content Factory 后台进程...
echo 日志文件: factory_output.txt
echo 统计文件: factory_stats.json
echo.

start "MiMo Factory" /b python mimo_factory.py > factory_output.txt 2>&1

echo 后台进程已启动
echo.
echo 查看日志: type factory_output.txt
echo 查看统计: python mimo_monitor_v2.py
echo 停止进程: taskkill /f /im python.exe /fi "WINDOWTITLE eq MiMo Factory*"
echo.

pause
