# Backend/GeminiBrain.py — Added Exit Command
import os
import requests
import json
import datetime
from dotenv import dotenv_values

# Load API Key
env_vars = dotenv_values(".Env")
GOOGLE_API_KEY = env_vars.get("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("Missing GOOGLE_API_KEY in .Env file")

class GeminiAgent:
    def __init__(self):
        self.history = []
        # Using Gemini 2.5 Flash
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GOOGLE_API_KEY}"
        
        # Inject Real Time
        now = datetime.datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
        
        # --- SYSTEM PROMPT ---
        self.system_prompt = {
            "role": "model",
            "parts": [{
                "text": (
                    f"System: Current Date/Time is {now}. "
                    "You are Proton, an advanced AI Assistant. "
                    "You can control the user's computer. "
                    # INSTRUCTIONS FOR COMMANDS:
                    "If the user asks to OPEN, START, or LAUNCH an app, reply exactly: COMMAND:OPEN:app_name "
                    "If the user asks to CLOSE, STOP, or KILL an app, reply exactly: COMMAND:CLOSE:app_name "
                    "If the user asks to SEARCH, reply exactly: COMMAND:SEARCH:query "
                    "If the user asks to EXIT, QUIT, or SHUTDOWN the bot, reply exactly: COMMAND:EXIT:GOODBYE "  # <--- NEW COMMAND
                    "For coding, math, or general chat, reply naturally. "
                )
            }]
        }
        self.history.append(self.system_prompt)

    def send_message(self, user_text):
        self.history.append({"role": "user", "parts": [{"text": user_text}]})

        # Robust Safety Settings
        safety_settings = [
            { "category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE" },
            { "category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE" },
            { "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE" },
            { "category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE" },
            { "category": "HARM_CATEGORY_CIVIC_INTEGRITY", "threshold": "BLOCK_NONE" } 
        ]

        payload = {
            "contents": self.history[-20:], 
            "generationConfig": {
                "temperature": 0.5,
                "maxOutputTokens": 8192 
            },
            "safetySettings": safety_settings
        }

        try:
            response = requests.post(
                self.url, 
                headers={"Content-Type": "application/json"}, 
                data=json.dumps(payload)
            )
            
            if response.status_code != 200:
                return f"API Error {response.status_code}: {response.text}"
            
            data = response.json()
            
            try:
                if "candidates" in data and len(data["candidates"]) > 0:
                    candidate = data["candidates"][0]
                    
                    # Handle Truncated/Empty Responses
                    if "content" in candidate and "parts" in candidate["content"]:
                        reply = candidate["content"]["parts"][0]["text"]
                    else:
                        reply = "Error: Content Blocked or Empty."
                else:
                    return "Error: Empty response from AI."

            except (KeyError, IndexError) as e:
                return f"Parsing Error: {str(e)}"

            self.history.append({"role": "model", "parts": [{"text": reply}]})
            return reply

        except Exception as e:
            return f"Connection Error: {e}"

bot = GeminiAgent()