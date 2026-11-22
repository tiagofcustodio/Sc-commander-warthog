@echo off
setlocal
title Star Citizen - HOTAS Warthog Commander PRO

:: Verifica se ja esta a correr como Administrador (necessario para gravar em C:\Program Files\Roberts Space Industries\... e injetar teclas no jogo)
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Solicitando privilegios de Administrador para sincronizar com o Star Citizen...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

echo ========================================================
echo    STAR CITIZEN - HOTAS WARTHOG COMMANDER PRO (4.10)
echo ========================================================
echo.

:: Procura pelo executavel do Python
set "PYTHON_EXE=C:\Users\tiago\AppData\Local\Programs\Python\Python311\python.exe"

if not exist "%PYTHON_EXE%" (
    where python >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        set "PYTHON_EXE=python"
    ) else (
        echo [ERRO] Python nao foi encontrado no sistema!
        echo Instale o Python 3.10+ ou verifique o caminho.
        pause
        exit /b 1
    )
)

cd /d "%~dp0\sc_warthog_commander"
echo A iniciar Warthog Commander PRO e a sincronizar perfis do Star Citizen...
"%PYTHON_EXE%" main.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo O programa encerrou com codigo %ERRORLEVEL%.
    pause
)
