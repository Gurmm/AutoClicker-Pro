@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
 echo Python launcher not found. Install Python on this BUILD computer first.
 pause
 exit /b 1
)
py -m pip install --upgrade pyinstaller pynput
if errorlevel 1 goto fail
py -m PyInstaller --noconfirm --clean --onefile --windowed --name AutoClicker_Pro src\auto_clicker_pro.py
if errorlevel 1 goto fail
echo.
echo Build complete: dist\AutoClicker_Pro.exe
pause
exit /b 0
:fail
echo Build failed.
pause
exit /b 1
