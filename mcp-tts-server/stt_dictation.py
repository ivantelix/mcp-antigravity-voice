import os
import re
import sys
import time
import asyncio
import tempfile
import threading
import subprocess
import pyperclip
import pyautogui
import speech_recognition as sr
from pynput import keyboard

# Suppress PyGame startup banner
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame
import edge_tts

# Configuration
WAKE_WORDS = ["gemini", "antigravity", "antigraviti"]
PROMPT_AUDIO_FILE = os.path.join(tempfile.gettempdir(), "tts_prompt_ready.mp3")

is_recording = False
recording_lock = threading.Lock()
current_pressed_keys = set()
last_hotkey_time = 0.0
stop_event = threading.Event()


def pregenerate_voice_prompt():
    """Pre-generates the voice prompt 'Sí Señor, ¿qué desea?' for instant low-latency audio playback."""
    try:
        if not os.path.exists(PROMPT_AUDIO_FILE):
            text = "Sí Señor, ¿qué desea?"
            communicate = edge_tts.Communicate(text, "es-ES-AlvaroNeural")
            asyncio.run(communicate.save(PROMPT_AUDIO_FILE))
    except Exception as e:
        print(f"[STT Setup] Warning pre-generating voice prompt: {e}")


def play_voice_prompt():
    """Plays 'Sí Señor, ¿qué desea?' spoken audio through default system speakers (with fallbacks for WSL/Linux)."""
    played = False
    try:
        pregenerate_voice_prompt()
        if os.path.exists(PROMPT_AUDIO_FILE):
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.music.load(PROMPT_AUDIO_FILE)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy() and not stop_event.is_set():
                time.sleep(0.05)
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
            played = True
    except Exception as e:
        print(f"[STT Audio Warning] Exception with pygame prompt playback: {e}")

    # Fallback playback for WSL/Linux if pygame fails or lacks audio device
    if not played and os.path.exists(PROMPT_AUDIO_FILE):
        try:
            if subprocess.call(["which", "ffplay"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
                subprocess.run(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", PROMPT_AUDIO_FILE], check=True)
            elif subprocess.call(["which", "paplay"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
                subprocess.run(["paplay", PROMPT_AUDIO_FILE], check=True, stderr=subprocess.DEVNULL)
            elif subprocess.call(["which", "mpg123"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
                subprocess.run(["mpg123", "-q", PROMPT_AUDIO_FILE], check=True)
            elif os.path.exists("/proc/sys/fs/binfmt_misc/WSLInterop") or os.getenv("WSL_DISTRO_NAME"):
                try:
                    win_path = subprocess.check_output(["wslpath", "-w", PROMPT_AUDIO_FILE]).decode().strip()
                    ps_cmd = f"Add-Type -AssemblyName presentationCore; $player = New-Object System.Windows.Media.MediaPlayer; $player.Open('{win_path}'); $player.Play(); Start-Sleep -s 3"
                    subprocess.run(["powershell.exe", "-Command", ps_cmd], check=True, stderr=subprocess.DEVNULL)
                except Exception as win_err:
                    print(f"[STT Audio Error] Windows PowerShell prompt playback failed: {win_err}")
        except Exception as fallback_err:
            print(f"[STT Audio Error] Fallback prompt playback failed: {fallback_err}")


def clean_transcript(text: str) -> str:
    """Removes wake word prefixes from transcript if present."""
    pattern = r'^\s*(gemini|antigravity|antigraviti)[\s,:]*'
    cleaned = re.sub(pattern, '', text, flags=re.IGNORECASE).strip()
    return cleaned if cleaned else text.strip()


def copy_to_clipboard(text: str):
    """Copies text to clipboard using pyperclip with fallback to Windows clip.exe in WSL."""
    if not text:
        return
    try:
        pyperclip.copy(text)
    except Exception as e:
        print(f"[STT Warning] Pyperclip error: {e}. Trying WSL Windows clip.exe fallback...")
        try:
            p = subprocess.Popen(['clip.exe'], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
            p.communicate(input=text.encode('utf-16-le'))
        except Exception as win_e:
            print(f"[STT Error] Could not copy to clipboard: {win_e}")


def paste_text_to_chat(text: str):
    """Copies transcribed text to clipboard and pastes into focused window."""
    if not text:
        return

    print(f"\n[STT Output] Transcrito exitosamente: \"{text}\"")

    copy_to_clipboard(text)
    time.sleep(0.15)

    pasted = False
    try:
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.1)
        pyautogui.press('enter')
        pasted = True
    except Exception as e:
        print(f"[STT Warning] PyAutoGUI paste failed: {e}. Trying WSL PowerShell SendKeys fallback...")

    if not pasted:
        try:
            ps_cmd = "$wshell = New-Object -ComObject wscript.shell; $wshell.SendKeys('^v'); Start-Sleep -m 100; $wshell.SendKeys('{ENTER}')"
            subprocess.run(["powershell.exe", "-Command", ps_cmd], check=True, stderr=subprocess.DEVNULL)
            pasted = True
        except Exception as win_e:
            print(f"[STT Error] Could not send paste hotkey: {win_e}")

    if pasted:
        print("[STT Output] Prompt enviado a Antigravity.")


def record_and_dictate():
    """Captures microphone audio, transcribes it to Spanish, and pastes it into chat."""
    global is_recording
    with recording_lock:
        if is_recording:
            return
        is_recording = True

    try:
        # 1. Play verbal prompt: "Sí Señor, ¿qué desea?"
        print("\n[STT Assistant] 🔊 \"Sí Señor, ¿qué desea?\"")
        play_voice_prompt()

        if stop_event.is_set():
            return

        recognizer = sr.Recognizer()
        recognizer.dynamic_energy_threshold = True
        recognizer.energy_threshold = 300
        recognizer.pause_threshold = 0.8

        print("[STT Assistant] 🎙️ Escuchando tu instrucción por el micrófono...")

        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.3)
            try:
                audio = recognizer.listen(source, timeout=8.0, phrase_time_limit=15.0)
                print("[STT Assistant] ⚙️ Procesando tu instrucción...")
                text = recognizer.recognize_google(audio, language="es-ES")
            except sr.WaitTimeoutError:
                print("[STT Assistant] ⚠️ Tiempo de espera agotado (no se detectó habla).")
                return
            except sr.UnknownValueError:
                print("[STT Assistant] ⚠️ No se entendió el audio o estuvo en silencio.")
                return
            except Exception as e:
                print(f"[STT Assistant] ⚠️ Error en reconocimiento: {e}")
                return

        cleaned_text = clean_transcript(text)
        if cleaned_text:
            paste_text_to_chat(cleaned_text)

    finally:
        with recording_lock:
            is_recording = False


def wake_word_listener():
    """Background thread continuously monitoring microphone for wake words ('Gemini' or 'Antigravity')."""
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True

    while not stop_event.is_set():
        if is_recording:
            time.sleep(0.5)
            continue

        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.3)
                try:
                    audio = recognizer.listen(source, timeout=4.0, phrase_time_limit=5.0)
                    if stop_event.is_set():
                        break
                    text = recognizer.recognize_google(audio, language="es-ES").lower()

                    # Check for wake words
                    if any(word in text for word in WAKE_WORDS):
                        print(f"\n[STT Wake Word] Palabra clave detectada: \"{text}\"")
                        prompt_after_wake = clean_transcript(text)

                        if prompt_after_wake and prompt_after_wake.lower() not in WAKE_WORDS:
                            paste_text_to_chat(prompt_after_wake)
                        else:
                            threading.Thread(target=record_and_dictate, daemon=True).start()

                except (sr.WaitTimeoutError, sr.UnknownValueError):
                    pass
                except Exception:
                    time.sleep(1)

        except Exception:
            time.sleep(2)


def on_press(key):
    """Hotkey event handler for Ctrl + Alt + V with debouncing."""
    global last_hotkey_time
    current_pressed_keys.add(key)

    is_ctrl = any(k in current_pressed_keys for k in [keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r])
    is_alt = any(k in current_pressed_keys for k in [keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr])
    is_v = False

    if hasattr(key, 'char') and key.char and key.char.lower() == 'v':
        is_v = True
    elif key == keyboard.KeyCode.from_char('v') or key == keyboard.KeyCode.from_char('V'):
        is_v = True

    if is_ctrl and is_alt and is_v:
        now = time.time()
        # Debounce: prevent multiple triggers within 2 seconds
        if now - last_hotkey_time > 2.0:
            last_hotkey_time = now
            print("\n[STT Hotkey] Atajo Ctrl+Alt+V detectado.")
            threading.Thread(target=record_and_dictate, daemon=True).start()


def on_release(key):
    """Hotkey key release handler."""
    try:
        current_pressed_keys.remove(key)
    except KeyError:
        pass


def main():
    print("=" * 60)
    print(" ASISTENTE LOCAL DE DICTADO POR VOZ (STT) PARA ANTIGRAVITY")
    print("=" * 60)
    print(" Pre-generando voz de confirmación...")
    pregenerate_voice_prompt()
    print(" ¡Voz de confirmación lista!")
    print("=" * 60)
    print(" Modos de activacion disponibles:")
    print("   1. Atajo de teclado: Presiona [Ctrl + Alt + V]")
    print("   2. Comando de Voz (Wake Word): Di 'Gemini' o 'Antigravity'")
    print(" Respondera en voz alta: \"Sí Señor, ¿qué desea?\"")
    print("=" * 60)
    print(" Presiona Ctrl + C en esta consola para detener.")
    print("=" * 60 + "\n")

    # Start Wake Word background thread (daemon)
    t_wake = threading.Thread(target=wake_word_listener, daemon=True)
    t_wake.start()

    # Start Global Hotkey Listener (daemon thread so Ctrl+C exits cleanly)
    try:
        listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        listener.daemon = True
        listener.start()
        print(" [STT Hotkey] Atajo [Ctrl + Alt + V] registrado correctamente.")
    except Exception as e:
        print(f" [STT Warning] No se pudo inicializar el atajo de teclado en Linux/WSL: {e}")
        print("               (Entorno sin servidor X11). El modo por voz ('Gemini' / 'Antigravity') sigue ACTIVO.")

    # Main thread loop allowing immediate Ctrl+C termination
    try:
        while not stop_event.is_set():
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\n[STT Assistant] Deteniendo servicio...")
        stop_event.set()
        try:
            if 'listener' in locals() and listener.is_alive():
                listener.stop()
        except Exception:
            pass
        print("[STT Assistant] Servicio detenido correctamente.")
        sys.exit(0)


if __name__ == "__main__":
    main()
