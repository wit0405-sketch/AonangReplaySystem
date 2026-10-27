@echo off
setlocal
cd /d "%~dp0"
echo =====================================================
echo AONANG LANDMARK REPLAY SYSTEM - Build Setup.exe
echo =====================================================
echo.
where py >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install Python 3.11 64-bit first.
  pause
  exit /b 1
)
py -3.11 -m pip install --upgrade pip
py -3.11 -m pip install -r requirements.txt
py -3.11 -m PyInstaller --noconfirm --windowed --name AonangReplaySystem --collect-all PySide6 src\main.py
if errorlevel 1 (
  echo Build failed while creating the app EXE.
  pause
  exit /b 1
)
where ISCC.exe >nul 2>nul
if errorlevel 1 (
  echo.
  echo Inno Setup compiler ISCC.exe was not found.
  echo Install Inno Setup 6, then run this file again.
  echo The official download page is https://jrsoftware.org/isinfo.php
  pause
  exit /b 1
)
ISCC.exe AONANG_REPLAY_SETUP.iss
if errorlevel 1 (
  echo Setup build failed. Check the messages above.
  pause
  exit /b 1
)
echo.
echo SUCCESS. Installer is in installer_output\Setup_AonangReplaySystem.exe
pause
