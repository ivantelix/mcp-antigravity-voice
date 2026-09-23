# Local Voice Suite: MCP Text-to-Speech (TTS) & STT Voice Dictation

Suite de voz local en Python para **Antigravity** (Soporta **WSL / Linux** y **Windows**):
1. **Salida de Voz (TTS):** Servidor MCP para que el agente te hable en voz alta.
2. **Entrada de Voz (STT):** Asistente de dictado en segundo plano para hablarle al agente por el micrófono.

---

## 🚀 Características

### 🔊 1. Salida de Voz (MCP TTS Server)
- **Protocolo MCP Estándar:** Implementado con `FastMCP` sobre transporte `stdio`.
- **Voces Neurales de Alta Calidad:** Utiliza `edge-tts` (`es-ES-AlvaroNeural`, `es-MX-JorgeNeural`).
- **Reproducción No Bloqueante & Multiplataforma:** Reproducción principal con `pygame` y fallbacks automáticos para WSL/Linux (`ffplay`, `paplay`, `mpg123`, `powershell.exe`).
- **Limpieza Automática de Texto:** Elimina código (```), URLs y Markdown antes de hablar.

### 🎙️ 2. Entrada de Voz (STT Dictation Assistant)
- **Activación Doble:** 
  - **Por Atajo:** Presionando `Ctrl + Alt + V`.
  - **Por Comando de Voz (Wake Word):** Pronunciando *"Gemini"* o *"Antigravity"*.
- **Tono Auditivo de Feedback:** Emite la confirmación *"Sí Señor, ¿qué desea?"* antes de escuchar.
- **Inyección Automática:** Transcribe tu habla a español y la pega directamente en la ventana activa de Antigravity (soporta fallbacks de portapapeles y pegado entre WSL y Windows Host).

---

## 📁 Estructura del Proyecto

```
mcp-tts-server/
├── .env.example              # Configuración de variables de entorno (voz por defecto)
├── pyproject.toml            # Configuración del paquete y dependencias Python
├── requirements.txt          # Lista de dependencias (TTS + STT)
├── server.py                 # Servidor MCP TTS (Herramienta speak_message)
├── stt_dictation.py          # Asistente de entrada de voz por micrófono
├── start_voice_assistant.sh  # Lanzador en 1-clic para WSL / Linux
├── start_voice_assistant.bat # Lanzador en 1-clic para Windows
└── README.md                 # Documentación e instrucciones
```

---

## 📦 Requisitos e Instalación

### En Linux / WSL:

1. **Instalar paquetes del sistema para audio, micrófono y Tkinter (GUI):**
   ```bash
   sudo apt update && sudo apt install -y portaudio19-dev python3-pyaudio alsa-utils ffmpeg xclip python3-tk python3-dev
   ```

2. **Entrar a la carpeta del proyecto:**
   ```bash
   ~/mcp-tts-server
   ```

3. **Crear entorno virtual e instalar dependencias:**
   ```bash
   uv venv .venv || python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

### En Windows (PowerShell / CMD):

1. **Entrar a la carpeta e instalar dependencias:**
   ```powershell
   cd C:\ruta\agentic-voice-mcp\mcp-tts-server
   uv venv .venv
   uv pip install -r requirements.txt
   ```

---

## 🎙️ Cómo Usar el Dictado por Voz (Entrada)

### En Linux / WSL:
Ejecuta el script ejecutable:
```bash
./start_voice_assistant.sh
```

### En Windows:
Haz doble clic en **`start_voice_assistant.bat`** o ejecútalo desde PowerShell:
```powershell
.\.venv\Scripts\python.exe stt_dictation.py
```

### Modos de uso:
- **Modo 1 (Atajo):** Haz clic en la caja de chat de Antigravity, presiona **`Ctrl + Alt + V`**, habla tu instrucción y el asistente la enviará automáticamente.
- **Modo 2 (Palabra Clave):** Di en voz alta *"Gemini, crea un script en Python que diga hola mundo"*. El asistente detectará la palabra clave, transcribirá la orden y la enviará al chat.

---

## ⚙️ Configuración del Servidor MCP TTS (Salida)

Agrega el bloque JSON correspondiente a tu archivo de configuración de servidores MCP (`mcp_config.json`):

### Para WSL / Linux:

```json
{
  "mcpServers": {
    "tts": {
      "command": "/$PATH/agentic-voice-mcp/mcp-tts-server/.venv/bin/python",
      "args": [
        "/$PATH/agentic-voice-mcp/mcp-tts-server/server.py"
      ],
      "env": {
        "DEFAULT_VOICE": "es-ES-AlvaroNeural"
      }
    }
  }
}
```

### Para Windows:

```json
{
  "mcpServers": {
    "tts": {
      "command": "C:/Users/$PATH/agentic-voice-mcp/mcp-tts-server/.venv/Scripts/python.exe",
      "args": [
        "C:/$PATH/agentic-voice-mcp/mcp-tts-server/server.py"
      ],
      "env": {
        "DEFAULT_VOICE": "es-ES-AlvaroNeural"
      }
    }
  }
}
```
