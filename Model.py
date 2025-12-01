# Backend/Model.py — High Speed Optimized
import os
import traceback
from dotenv import dotenv_values

# --- Load Env ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
env_path = os.path.join(PROJECT_ROOT, ".Env")
env_vars = dotenv_values(env_path)

CohereAPIKey = env_vars.get("COHERE_API_KEY")
MODEL_NAME = "command-a-03-2025"

co = None
if CohereAPIKey:
    try:
        import cohere
        co = cohere.Client(api_key=CohereAPIKey)
    except Exception as e:
        print(f"[Model] Error init Cohere: {e}")

# --- 1. Fast Local Decisions (0ms Latency) ---
def _heuristic_check(prompt: str):
    """
    Checks for common keywords to avoid calling the AI API.
    Returns the decision list if found, else None.
    """
    p = prompt.lower().strip()
    
    # Automation Keywords
    if p.startswith(("open", "close", "launch", "start", "stop", "kill", "play", "google search")):
        return [p] # Return the command as-is (e.g., "open chrome")

    # Realtime Information Keywords
    # If user asks for time, date, weather, or specific "who is" questions
    rt_triggers = [
        "time", "date", "day is it", "weather", "news", 
        "score", "stock", "price", "who is", "what is", 
        "where is", "how to", "search"
    ]
    if any(t in p for t in rt_triggers):
        return [f"realtime {p}"]

    return None

def _extract_decisions(text: str):
    """Parses AI response looking for keywords."""
    text = text.lower().strip()
    if "realtime" in text: return [f"realtime {text.replace('realtime', '').strip()}"]
    if "general" in text: return [f"general {text.replace('general', '').strip()}"]
    return []

# --- 2. Main Decision Function ---
def FirstLayerDMM(prompt: str = "test"):
    print(f"[DMM] Processing: '{prompt}'")

    # STEP 1: Try Heuristic (Instant)
    # We check this FIRST to save time.
    fast_decision = _heuristic_check(prompt)
    if fast_decision:
        print(f"[DMM] Fast Heuristic Match: {fast_decision}")
        return fast_decision

    # STEP 2: Try Cohere Chat (Only if Heuristic failed)
    if co:
        try:
            # Stronger System Prompt to force strict categorization
            preamble = (
                "You are a routing system. You do not answer questions. "
                "You only categorize prompts into two types: "
                "1. 'realtime <query>' (if it needs web search, current data, or facts). "
                "2. 'general <query>' (if it is chit-chat, creative writing, or coding). "
                "Reply ONLY with the category string."
            )
            
            # Using Chat endpoint as Generate is deprecated
            resp = co.chat(model=MODEL_NAME, message=prompt, preamble=preamble, temperature=0.1)
            text = getattr(resp, "text", "") or str(resp)
            
            print(f"[DMM] AI Response: {text}")
            
            # Parse output
            if "realtime" in text.lower():
                return [f"realtime {prompt}"]
            elif "general" in text.lower():
                return [f"general {prompt}"]
                
        except Exception as e:
            print(f"[DMM] AI Error: {e}")

    # STEP 3: Fallback (Safe Default)
    print("[DMM] Fallback to General.")
    return [f"general {prompt}"]