# Backend/TextToSpeech.py (patched robust TTS)
import os
import time
import threading
import asyncio
import edge_tts
import pygame
from dotenv import dotenv_values

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
env = dotenv_values(os.path.join(PROJECT_ROOT, ".Env"))
AssistantVoice = env.get("AssistantVoice", "en-GB-RyanNeural")

DATA_SPEECH = os.path.join(PROJECT_ROOT, "Data", "speech.mp3")
os.makedirs(os.path.dirname(DATA_SPEECH), exist_ok=True)

async def _text_to_audio_file_async(text: str, path: str):
    # use edge_tts Communicate.save
    comm = edge_tts.Communicate(text, AssistantVoice)
    await comm.save(path)

def _run_coroutine_in_thread(coro, *args, **kwargs):
    """
    Run coroutine in a new event loop within a thread and wait for completion.
    Returns the coroutine result or raises.
    """
    result_container = {}
    exc_container = {}

    def runner():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            res = loop.run_until_complete(coro(*args, **kwargs))
            result_container['res'] = res
            loop.close()
        except Exception as e:
            exc_container['exc'] = e

    t = threading.Thread(target=runner)
    t.start()
    t.join()
    if 'exc' in exc_container:
        raise exc_container['exc']
    return result_container.get('res', None)

def _play_audio_file(path: str):
    try:
        # Wait briefly until file is non-empty
        wait = 0
        while (not os.path.exists(path) or os.path.getsize(path) < 1000) and wait < 8:
            time.sleep(0.2)
            wait += 0.2
        if not os.path.exists(path) or os.path.getsize(path) < 1000:
            print("[TTS] Audio file missing or too small:", path)
            return False

        pygame.mixer.init()
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(30)
        pygame.mixer.music.stop()
        try:
            pygame.mixer.quit()
        except:
            pass
        return True
    except Exception as e:
        print("[TTS] play error:", e)
        try:
            pygame.mixer.quit()
        except:
            pass
        return False

def TextToSpeech(Text: str):
    if not Text:
        return False
    try:
        # For long text, you may shorten to preview
        text_to_speak = Text if len(Text) <= 300 else Text[:300] + " ..."

        # Generate audio file in thread-safe coroutine runner
        _run_coroutine_in_thread(_text_to_audio_file_async, text_to_speak, DATA_SPEECH)

        # Play audio (blocking until done)
        return _play_audio_file(DATA_SPEECH)
    except Exception as e:
        print("[TTS] Error in TextToSpeech:", e)
        return False
