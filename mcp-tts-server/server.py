import os
import re
import tempfile
import threading
import time
import asyncio
import subprocess
from typing import Dict, Any, Optional

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Suppress pygame startup banner
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame

# Load environment variables if .env exists
load_dotenv()

DEFAULT_VOICE = os.getenv("DEFAULT_VOICE", "es-ES-AlvaroNeural")

# Initialize FastMCP Server
mcp = FastMCP("TTS Server")


def clean_text_for_speech(text: str) -> str:
    """
    Cleans markdown formatting, code blocks, URLs, and noisy characters
    to ensure smooth and natural text-to-speech pronunciation.
    """
    if not text:
        return ""

    # 1. Remove code blocks ```...```
    cleaned = re.sub(r'```[\s\S]*?```', '', text, flags=re.DOTALL)

    # 2. Remove markdown horizontal rules (---, ***, ___)
    cleaned = re.sub(r'^\s*[-*_]{3,}\s*$', '', cleaned, flags=re.MULTILINE)

    # 3. Remove markdown tables (lines starting and ending with |)
    cleaned = re.sub(r'^\s*\|.*\|\s*$', '', cleaned, flags=re.MULTILINE)

    # 4. Remove URLs
    cleaned = re.sub(r'https?://\S+|www\.\S+', 'enlace', cleaned)

    # 5. Clean markdown links [text](url) -> text
    cleaned = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', cleaned)

    # 6. Remove inline backticks `code` -> code
    cleaned = re.sub(r'`([^`]+)`', r'\1', cleaned)

    # 7. Remove headers (# Header)
    cleaned = re.sub(r'#+\s*', '', cleaned)

    # 8. Remove bold/italic formatting (*bold*, **bold**, _italic_, __italic__)
    cleaned = re.sub(r'[*_]{1,3}([^*_]+)[*_]{1,3}', r'\1', cleaned)

    # 9. Remove markdown bullet symbols at start of lines
    cleaned = re.sub(r'^\s*[-*+]\s+', '', cleaned, flags=re.MULTILINE)

    # 10. Remove HTML tags
    cleaned = re.sub(r'<[^>]+>', '', cleaned)

    # 11. Normalize multiple whitespace and line breaks
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    return cleaned


def _play_audio_file(file_path: str) -> None:
    """
    Plays an MP3 audio file using pygame.mixer in a thread (with fallbacks for WSL/Linux),
    then cleans up the temporary file after playback completes.
    """
    played = False
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            time.sleep(0.05)

        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
        played = True
    except Exception as e:
        print(f"[TTS Audio Warning] Pygame playback issue: {e}")

    # Fallback playback for WSL/Linux if pygame fails or lacks audio device
    if not played and os.path.exists(file_path):
        try:
            if subprocess.call(["which", "ffplay"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
                subprocess.run(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", file_path], check=True)
            elif subprocess.call(["which", "paplay"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
                subprocess.run(["paplay", file_path], check=True, stderr=subprocess.DEVNULL)
            elif subprocess.call(["which", "mpg123"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
                subprocess.run(["mpg123", "-q", file_path], check=True)
            elif os.path.exists("/proc/sys/fs/binfmt_misc/WSLInterop") or os.getenv("WSL_DISTRO_NAME"):
                try:
                    win_path = subprocess.check_output(["wslpath", "-w", file_path]).decode().strip()
                    ps_cmd = f"Add-Type -AssemblyName presentationCore; $player = New-Object System.Windows.Media.MediaPlayer; $player.Open('{win_path}'); $player.Play(); Start-Sleep -s 4"
                    subprocess.run(["powershell.exe", "-Command", ps_cmd], check=True, stderr=subprocess.DEVNULL)
                except Exception as win_err:
                    print(f"[TTS Audio Error] Windows PowerShell audio fallback failed: {win_err}")
        except Exception as fallback_err:
            print(f"[TTS Audio Error] Fallback audio playback failed: {fallback_err}")

    # Cleanup temporary audio file
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError:
            pass


@mcp.tool()
async def speak_message(text: str, voice: Optional[str] = None) -> Dict[str, Any]:
    """
    Sintetiza y reproduce un mensaje en voz alta usando Microsoft Edge Neural TTS.

    :param text: El mensaje, resumen o pregunta a reproducir en voz alta.
    :param voice: Voz a utilizar (ej: es-ES-AlvaroNeural, es-MX-JorgeNeural). Por defecto usa es-ES-AlvaroNeural.
    :return: Estado de ejecucion y longitud del texto procesado.
    """
    import edge_tts

    selected_voice = voice if voice else DEFAULT_VOICE
    clean_text = clean_text_for_speech(text)

    if not clean_text:
        return {"status": "skipped", "reason": "Empty text after cleaning", "length": 0}

    # Generate TTS audio file
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
        temp_file_path = temp_file.name

    communicate = edge_tts.Communicate(clean_text, selected_voice)
    await communicate.save(temp_file_path)

    # Play audio in a thread pool without blocking asyncio event loop,
    # ensuring playback completes before temporary file cleanup and return
    await asyncio.to_thread(_play_audio_file, temp_file_path)

    return {
        "status": "spoken",
        "length": len(clean_text),
        "voice": selected_voice,
        "preview": clean_text[:100] + ("..." if len(clean_text) > 100 else "")
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
