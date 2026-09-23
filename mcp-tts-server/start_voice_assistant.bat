@echo off
title Asistente de Voz Antigravity (STT Dictado)
color 0B
echo.
echo =========================================================
echo   Iniciando Asistente de Dictado por Voz (STT)...
echo =========================================================
echo.
cd /d "%~dp0"
.\.venv\Scripts\python.exe stt_dictation.py
pause
