@echo off
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION
title Build Bot_WnS (Console Mode)

echo ============================================
echo    GERANDO EXECUTAVEL DO BOT_WnS (.EXE)
echo    Modo: Console (logs visíveis)
echo ============================================
echo.

:: Ativa o ambiente virtual (ajuste o caminho se precisar)
call .\.venv\Scripts\activate.bat

:: Garante que o PyInstaller está atualizado
echo Instalando/atualizando o PyInstaller...
python -m pip install --upgrade pip
python -m pip install --upgrade pyinstaller

:: Limpeza de compilações anteriores
if exist build rd /s /q build
if exist dist rd /s /q dist
if exist __pycache__ rd /s /q __pycache__
del /q /f *.spec 2>nul

:: Define nomes e arquivos
set NAME=Bot_WnS
set ENTRY=monitor.py

:: Compilação com console
echo.
echo Compilando o executável com console...
pyinstaller --onefile --console --name %NAME% %ENTRY%
set ERR=%ERRORLEVEL%

:: Verificação de erro na compilação
if not "%ERR%"=="0" (
    echo.
    echo ERRO na compilacao! Codigo: %ERR%
    echo Abortando...
    pause
    exit /b %ERR%
)

:: Exibe o resultado final
echo.
echo ============================================
echo   BUILD FINALIZADO COM SUCESSO
echo   ARQUIVO GERADO:
echo   %cd%\dist\%NAME%.exe
echo ============================================

pause
endlocal
