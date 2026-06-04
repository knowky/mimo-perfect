@echo off
REM MiMo Token Burner - 后台启动脚本
REM 使用 start /b 在后台运行

cd /d "%~dp0"

echo 启动 MiMo Token Burner 后台进程...
echo 日志文件: burner_output.txt
echo 统计文件: burn_stats.json
echo.

start "MiMo Burner" /b python mimo_burner.py > burner_output.txt 2>&1

echo 后台进程已启动
echo 使用以下命令查看日志:
echo   type burner_output.txt
echo.
echo 使用以下命令查看统计:
echo   python mimo_monitor.py
echo.
echo 使用以下命令停止:
echo   taskkill /f /im python.exe /fi "WINDOWTITLE eq MiMo Burner*"

pause
