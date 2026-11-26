@echo off
setlocal
echo ========================================================
echo   Building SC_Warthog_Commander.exe (Standalone)
echo ========================================================

set "PYTHON_EXE=C:\Users\tiago\AppData\Local\Programs\Python\Python311\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"

cd /d "%~dp0"
"%PYTHON_EXE%" -m PyInstaller --clean --noconfirm SC_Warthog_Commander.spec

if %ERRORLEVEL% neq 0 (
    echo [ERROR] Build failed with code %ERRORLEVEL%.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [OK] Standalone executable built at: dist\SC_Warthog_Commander.exe
pause
