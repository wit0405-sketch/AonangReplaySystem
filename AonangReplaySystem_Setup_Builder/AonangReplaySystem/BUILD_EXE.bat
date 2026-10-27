@echo off
cd /d "%~dp0"
py -3.11 -m PyInstaller --noconfirm --windowed --name AonangReplaySystem --collect-all PySide6 src\main.py
if errorlevel 1 py -m PyInstaller --noconfirm --windowed --name AonangReplaySystem --collect-all PySide6 src\main.py
echo.
echo Build finished. Check dist\AonangReplaySystem\
pause
