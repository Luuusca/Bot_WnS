@echo off
title Build Bot_WnS
echo ============================================
echo   GERANDO EXECUTAVEL DO BOT_WNS (.EXE)
echo ============================================
echo.

REM Ativa o ambiente virtual
call .\.venv\Scripts\activate.bat

REM Garante que o PyInstaller está instalado/atualizado
echo Instalando/atualizando o PyInstaller...
python -m pip install --upgrade pip
python -m pip install --upgrade pyinstaller

REM Compila o projeto em um único .exe (sem console)
echo.
echo Compilando o executavel...
pyinstaller --onefile --noconsole --name Bot_WnS monitor.py

REM Exibe o caminho do executável
echo.
echo ============================================
echo   BUILD FINALIZADO COM SUCESSO!
echo   O ARQUIVO FOI GERADO EM:
echo   %cd%\dist\Bot_WnS.exe
echo ============================================

pause