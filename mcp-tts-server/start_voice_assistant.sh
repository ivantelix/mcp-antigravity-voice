#!/usr/bin/env bash
# Script de inicio del asistente de dictado por voz (STT) para WSL / Linux

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -f ".venv/bin/python" ]; then
    PYTHON_BIN=".venv/bin/python"
elif [ -f "../.venv/bin/python" ]; then
    PYTHON_BIN="../.venv/bin/python"
else
    PYTHON_BIN="python3"
fi

echo "========================================================="
echo "  Iniciando Asistente de Dictado por Voz (STT) [WSL/Linux]"
echo "========================================================="
$PYTHON_BIN stt_dictation.py
