# systems/audio.py
import os
import threading
import pygame

# Try to import pyttsx3 only if available.
try:
    import pyttsx3
    TTS_AVAILABLE = True
except Exception:
    TTS_AVAILABLE = False

# initialize pygame mixer for .wav/.mp3 (ignore errors)
try:
    pygame.mixer.init()
except Exception as e:
    print("pygame.mixer.init() error:", e)

def _tts_speak(word):
    """Create a local engine in a thread so pyttsx3 doesn't block main thread."""
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 170)
        engine.setProperty("volume", 1.0)
        engine.say(word)
        engine.runAndWait()
    except Exception as e:
        print("TTS thread error:", e)

def speak_word(word, audio_path=None):
    """
    Play an audio file if available (non-blocking). Otherwise speak the word using pyttsx3 in a thread.
    """
    # 1) If an audio file path exists, play it non-blocking via pygame.mixer.Sound
    if audio_path:
        try:
            if os.path.exists(audio_path):
                snd = pygame.mixer.Sound(audio_path)
                snd.play()
                return
        except Exception as e:
            # If file playback fails, fall back to TTS
            print("Audio file playback error:", e)

    # 2) Fallback: use pyttsx3 TTS in a background thread (so UI doesn't freeze)
    if TTS_AVAILABLE:
        try:
            t = threading.Thread(target=_tts_speak, args=(word,), daemon=True)
            t.start()
        except Exception as e:
            print("Failed to start TTS thread:", e)
    else:
        # If pyttsx3 isn't available, just silently ignore (or print)
        print("TTS not available and no audio file for:", word)
