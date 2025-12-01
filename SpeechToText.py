# Backend/SpeechToText.py — Optimized Continuous Listening
import speech_recognition as sr
import os

# --- GLOBAL INIT (Run once to prevent lag) ---
recognizer = sr.Recognizer()
recognizer.dynamic_energy_threshold = False # Prevent auto-gain from fluctuating
recognizer.energy_threshold = 400 # Fixed sensitivity (adjust 300-500 if needed)

# Reuse the same microphone source
mic_source = sr.Microphone()

# Calibrate ONLY ONCE at startup
try:
    with mic_source as source:
        print("[SpeechToText] Calibrating silence... (Please be quiet)")
        recognizer.adjust_for_ambient_noise(source, duration=1.0)
        print("[SpeechToText] Calibration Complete. Mic Ready.")
except Exception as e:
    print(f"[SpeechToText] Mic Init Error: {e}")

def SpeechRecognition():
    """
    Uses Google's Online Speech Recognition API.
    Now optimized for continuous speed.
    """
    try:
        with mic_source as source:
            # Listen with a hard timeout to keep the loop moving
            # timeout=wait for speech to start
            # phrase_time_limit=max duration of command
            audio = recognizer.listen(source, timeout=None, phrase_time_limit=5)
            
            print("[SpeechToText] Processing...")
            text = recognizer.recognize_google(audio, language="en-US")
            text = text.lower().strip()
            
            print(f"[SpeechToText] Recognized: '{text}'")
            return text

    except sr.WaitTimeoutError:
        return "" 
    except sr.UnknownValueError:
        return "" 
    except sr.RequestError:
        print("[SpeechToText] Internet/API Error.")
        return ""
    except Exception as e:
        # Sometimes PyAudio throws overflow errors, just ignore and retry
        return ""