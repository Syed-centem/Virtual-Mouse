# Backend/SpeechToText.py — Google Online Version (High Accuracy)
import speech_recognition as sr
import os

def SpeechRecognition():
    """
    Uses Google's Online Speech Recognition API.
    Requires: pip install SpeechRecognition pyaudio
    """
    recognizer = sr.Recognizer()
    
    # Adjust sensitivity (Lower = more sensitive)
    recognizer.energy_threshold = 300  
    recognizer.dynamic_energy_threshold = True

    try:
        with sr.Microphone() as source:
            print("[SpeechToText] Adjusting for ambient noise...")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
            print("[SpeechToText] Listening...")
            # Listen for input (stops automatically when you stop speaking)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)
            
            print("[SpeechToText] Recognizing...")
            # Send audio to Google servers
            text = recognizer.recognize_google(audio, language="en-US")
            
            # Clean up text
            text = text.lower().strip()
            print(f"[SpeechToText] Recognized: '{text}'")
            return text

    except sr.WaitTimeoutError:
        return "" # No speech detected
    except sr.UnknownValueError:
        return "" # Speech was unintelligible
    except sr.RequestError:
        print("[SpeechToText] Internet connection failed.")
        return ""
    except Exception as e:
        print(f"[SpeechToText] Error: {e}")
        return ""