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
if errorlevel 1 goto :fail
py -3.11 -m pip install -r requirements.txt
if errorlevel 1 goto :fail
py -3.11 -m PyInstaller --noconfirm --clean --windowed --name AonangReplaySystem --collect-all PySide6 --collect-all cv2 --collect-all obsws_python src\main.py
if errorlevel 1 goto :fail
where ISCC.exe >nul 2>nul
if errorlevel 1 (
  echo Inno Setup compiler ISCC.exe was not found.
  echo Install Inno Setup 6 from https://jrsoftware.org/isinfo.php
  pause
  exit /b 1
)
ISCC.exe AONANG_REPLAY_SETUP.iss
if errorlevel 1 goto :fail
if not exist "installer_output\Setup_AonangReplaySystem.exe" goto :fail
echo.
echo SUCCESS: installer_output\Setup_AonangReplaySystem.exe
pause
exit /b 0

:fail
echo.
echo BUILD FAILED. Review the error messages above.
pause
exit /b 1
