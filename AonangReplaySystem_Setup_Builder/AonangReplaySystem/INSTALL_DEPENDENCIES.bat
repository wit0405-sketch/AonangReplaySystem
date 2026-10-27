@echo off
cd /d "%~dp0"
echo Installing dependencies for AONANG REPLAY SYSTEM...
py -3.11 -m pip install --upgrade pip
if errorlevel 1 py -m pip install --upgrade pip
py -3.11 -m pip install -r requirements.txt
if errorlevel 1 py -m pip install -r requirements.txt
echo.
echo Done. If there were errors, install Python 3.11 64-bit and retry.
pause
