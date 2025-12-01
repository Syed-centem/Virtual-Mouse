# Backend/Chatbot.py
"""
Patched ChatBot wrapper:
- Robust to different cohere SDKs.
- Sanitizes output (removes ** and excessive whitespace).
- Always returns a string; never raises to caller.
"""

import os
import traceback
from json import load, dump
from dotenv import dotenv_values

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
ENV_PATH = os.path.join(PROJECT_ROOT, ".Env")
env = dotenv_values(ENV_PATH)

COHERE_API_KEY = env.get("COHERE_API_KEY")
Username = env.get("Username", "User")
Assistantname = env.get("Assistantname", "Assistant")

MODEL_NAME = "command-a-03-2025"

# init client if possible
client = None
if COHERE_API_KEY:
    try:
        import cohere as _co
        client = _co.Client(api_key=COHERE_API_KEY)
        print("[ChatBot] Cohere client ready.")
    except Exception as e:
        print("[ChatBot] Cohere init failed:", e)
        client = None
else:
    print("[ChatBot] No COHERE_API_KEY in .Env")

CHATLOG_PATH = os.path.join(PROJECT_ROOT, "Data", "ChatLog.json")
os.makedirs(os.path.dirname(CHATLOG_PATH), exist_ok=True)
if not os.path.exists(CHATLOG_PATH):
    with open(CHATLOG_PATH, "w", encoding="utf-8") as f:
        dump([], f)

def RealtimeInformation():
    import datetime
    now = datetime.datetime.now()
    return f"Day: {now.strftime('%A')}\nDate: {now.strftime('%d %B %Y')}\nTime: {now.strftime('%H:%M:%S')}"

def AnswerModifier(answer: str) -> str:
    """Sanitize assistant text (remove markdown bold and collapse whitespace)."""
    if not answer:
        return ""
    s = answer.replace("**", "")        # remove bold markers
    s = s.replace("`", "")             # remove backticks
    # collapse multiple spaces/newlines
    parts = [line.strip() for line in s.splitlines()]
    joined = "\n".join([p for p in parts if p])
    # further collapse to single spaces on lines if extremely long
    return joined

def ChatBot(Query: str) -> str:
    """Return assistant reply text for Query. Never raise; always return string."""
    # load chat history (best-effort)
    try:
        with open(CHATLOG_PATH, "r", encoding="utf-8") as f:
            messages = load(f)
    except Exception:
        messages = []

    messages.append({"role": "user", "content": Query})
    answer_text = None

    if client:
        # 1) try modern client.chat
        try:
            if hasattr(client, "chat"):
                try:
                    resp = client.chat(model=MODEL_NAME, message=Query, temperature=0.6)
                    answer_text = getattr(resp, "text", None) or str(resp)
                except Exception as e:
                    print("[ChatBot] client.chat error:", e)
                    traceback.print_exc()
                    answer_text = None
        except Exception as e:
            print("[ChatBot] Unexpected client.chat block error:", e)
            traceback.print_exc()

        # 2) try generate fallback
        if not answer_text and hasattr(client, "generate"):
            try:
                resp = client.generate(model=MODEL_NAME, prompt=f"Answer concisely: {Query}", max_tokens=300)
                gens = getattr(resp, "generations", None)
                if gens and len(gens) > 0:
                    answer_text = getattr(gens[0], "text", None) or str(gens[0])
                else:
                    answer_text = str(resp)
            except Exception as e:
                print("[ChatBot] client.generate error:", e)
                traceback.print_exc()
                answer_text = None

        # 3) try chat_stream last
        if not answer_text and hasattr(client, "chat_stream"):
            try:
                buf = ""
                stream = client.chat_stream(model=MODEL_NAME, message=Query, temperature=0.6)
                for ev in stream:
                    buf += getattr(ev, "text", "") or ""
                answer_text = buf
            except Exception as e:
                print("[ChatBot] client.chat_stream error:", e)
                traceback.print_exc()
                answer_text = None

    # final fallback if no client or all failed
    if not answer_text:
        answer_text = f"Sorry, the remote assistant is unavailable. I can still attempt to help: {Query}"

    # sanitize
    try:
        answer_text = AnswerModifier(answer_text)
    except Exception as e:
        print("[ChatBot] AnswerModifier failed:", e)
        traceback.print_exc()

    # save to chat log (best-effort)
    try:
        messages.append({"role": "assistant", "content": answer_text})
        messages = messages[-100:]
        with open(CHATLOG_PATH, "w", encoding="utf-8") as f:
            dump(messages, f, indent=2)
    except Exception as e:
        print("[ChatBot] Failed to save chatlog:", e)
        traceback.print_exc()

    return answer_text

