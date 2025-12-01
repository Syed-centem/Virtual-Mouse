# Frontend/GUI.py
# Clean, modern-ish Tkinter chat UI that integrates with the existing file-based backend.
# Exposes functions expected by Main.py

import tkinter as tk
from tkinter import ttk, scrolledtext
from datetime import datetime
import threading
import os
import json
import time
import pathlib
import textwrap
import html
from collections import deque

# ---- Configuration ----
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FILES_DIR = os.path.join(ROOT_DIR, "Frontend", "Files")
DATA_DIR = os.path.join(ROOT_DIR, "Data")

os.makedirs(FILES_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

DB_FILE = os.path.join(FILES_DIR, "Database.data")
RESP_FILE = os.path.join(FILES_DIR, "Responses.data")
MIC_FILE = os.path.join(FILES_DIR, "Mic.data")
STATUS_FILE = os.path.join(FILES_DIR, "Status.data")
CHATLOG_FILE = os.path.join(DATA_DIR, "ChatLog.json")


# ---- Utility helpers (file-backed state used by Main.py) ----
def TempDirectoryPath(name: str) -> str:
    return os.path.join(FILES_DIR, name)

def read_file(path, default=""):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return default

def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def append_chatlog(role, content):
    # Append to Data/ChatLog.json in required format
    try:
        if not os.path.exists(CHATLOG_FILE):
            write_file(CHATLOG_FILE, "[]")
        with open(CHATLOG_FILE, "r+", encoding="utf-8") as f:
            data = json.load(f)
            data.append({"role": role, "content": content})
            f.seek(0)
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.truncate()
    except Exception as e:
        print("[GUI] append_chatlog error:", e)

# ---- Simple text cleanup for assistant responses (strip markdown markers, code fences) ----
def AnswerModifier(text: str) -> str:
    if text is None:
        return ""
    # basic cleanup: remove triple backticks, bold markers (** or __), and excessive blank lines
    out = text.replace("```", "\n")
    out = out.replace("**", "")
    out = out.replace("__", "")
    # remove leading/trailing whitespace and normalize newlines
    lines = [ln.rstrip() for ln in out.splitlines()]
    # compact multiple empty lines
    cleaned = []
    blank = False
    for ln in lines:
        if ln.strip() == "":
            if not blank:
                cleaned.append("")
            blank = True
        else:
            cleaned.append(ln)
            blank = False
    return "\n".join(cleaned).strip()

def QueryModifier(q: str) -> str:
    # place for query normalization; for now just return stripped text
    return (q or "").strip()

def SetMicrophoneStatus(value: str):
    # value expected "True"/"False"
    write_file(MIC_FILE, str(value))

def GetMicrophoneStatus():
    s = read_file(MIC_FILE, default="False").strip()
    return s

def SetAssistantStatus(status: str):
    write_file(STATUS_FILE, str(status))

def GetAssistantStatus():
    return read_file(STATUS_FILE, default="Available ...")

def ShowTextToScreen(text: str):
    # Write assistant text to Responses.data (used by previous code expectations)
    write_file(RESP_FILE, text)

# ---- UI: Chat bubble logic ----
MAX_BUBBLE_WIDTH = 60  # characters for textwrap

def format_bubble(message: str, who: str):
    # message -> lines wrapped, add timestamp
    ts = datetime.now().strftime("%H:%M")
    wrapped = textwrap.fill(message, width=MAX_BUBBLE_WIDTH)
    return wrapped + "\n\n" + ts

# ---- Tkinter UI ----
class ChatGUI(tk.Tk):
    POLL_INTERVAL = 600  # ms

    def __init__(self):
        super().__init__()
        self.title("Proton — AI Virtual Assistant")
        self.geometry("1100x700")
        self.configure(bg="#f4f4f4")
        self.minsize(800, 500)

        # top bar
        top = ttk.Frame(self)
        top.pack(side="top", fill="x", padx=10, pady=6)
        self.title_label = ttk.Label(top, text="Proton", font=("Helvetica", 18, "bold"))
        self.title_label.pack(side="left")
        self.subtitle = ttk.Label(top, text="Assistant — speak or type below", font=("Helvetica", 10))
        self.subtitle.pack(side="left", padx=10)

        # main frame with left chat and right panel
        main = ttk.Frame(self)
        main.pack(fill="both", expand=True, padx=10, pady=(0,10))

        # left: chat frame
        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True)

        self.chat_canvas = tk.Canvas(left, bg="#1f1f1f", highlightthickness=0)
        self.chat_scroll = ttk.Scrollbar(left, orient="vertical", command=self.chat_canvas.yview)
        self.chat_frame = ttk.Frame(self.chat_canvas)

        self.chat_frame.bind(
            "<Configure>",
            lambda e: self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))
        )
        self.chat_canvas.create_window((0,0), window=self.chat_frame, anchor="nw")
        self.chat_canvas.configure(yscrollcommand=self.chat_scroll.set)

        self.chat_canvas.pack(side="left", fill="both", expand=True)
        self.chat_scroll.pack(side="right", fill="y")

        # message widgets list
        self._message_widgets = deque(maxlen=200)

        # right large panel for images / visual results
        right = ttk.Frame(main, width=320)
        right.pack(side="right", fill="y")
        self.preview = tk.Label(right, text="Preview panel", background="#222", fg="#ddd", width=40, height=35, anchor="center", justify="center")
        self.preview.pack(expand=True, fill="both", padx=(10,0))

        # bottom entry area (type + mic)
        bottom = ttk.Frame(self)
        bottom.pack(side="bottom", fill="x", padx=10, pady=8)

        self.entry_var = tk.StringVar()
        self.entry = ttk.Entry(bottom, textvariable=self.entry_var)
        self.entry.pack(side="left", fill="x", expand=True, padx=(0,6))
        self.entry.bind("<Return>", self._on_send)

        self.send_btn = ttk.Button(bottom, text="Send", command=self._on_send)
        self.send_btn.pack(side="left")

        self.mic_state = tk.StringVar(value=GetMicrophoneStatus())
        self.mic_btn = ttk.Button(bottom, text="Start Mic" if self.mic_state.get()!="True" else "Stop Mic", command=self._toggle_mic)
        self.mic_btn.pack(side="left", padx=(6,0))

        self.status_label = ttk.Label(bottom, text=GetAssistantStatus())
        self.status_label.pack(side="right")

        # initial read of existing conversations
        self._last_resp = ""
        self._last_db = ""
        self._load_initial_files()

        # Start polling
        self.after(200, self._poll_files)

    # UI helpers
    def _add_message(self, who: str, text: str):
        # who: "user" or "assistant"
        text = AnswerModifier(text)
        bubble = tk.Label(self.chat_frame, text=text, bg="#0084ff" if who=="user" else "#2f2f2f",
                          fg="#fff" if who=="user" else "#eee", justify="left",
                          wraplength=520, padx=12, pady=8, anchor="w")
        ts = tk.Label(self.chat_frame, text=datetime.now().strftime("%H:%M"), bg=self.chat_frame.cget("background"),
                      fg="#aaa", font=("Helvetica", 8))
        # layout
        if who == "user":
            bubble.pack(anchor="e", padx=10, pady=6)
            ts.pack(anchor="e", padx=10)
        else:
            bubble.pack(anchor="w", padx=10, pady=6)
            ts.pack(anchor="w", padx=10)

        self._message_widgets.append((bubble, ts))
        # keep canvas scrolled to bottom
        self.chat_canvas.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)

    def _load_initial_files(self):
        # populate chat with Database.data and Responses.data if available
        db = read_file(DB_FILE, "")
        resp = read_file(RESP_FILE, "")
        if db:
            # show as previous user lines - simple split
            for line in db.splitlines():
                if line.strip():
                    self._add_message("user", line.strip())
        if resp:
            self._add_message("assistant", resp.strip())

    def _poll_files(self):
        # read response file -> update if changed
        try:
            resp = read_file(RESP_FILE, "")
            if resp != self._last_resp and resp.strip():
                self._last_resp = resp
                self._add_message("assistant", resp)
                self.status_label.config(text=GetAssistantStatus())
            db = read_file(DB_FILE, "")
            if db != self._last_db and db.strip():
                # new user content
                # We take last non-empty line as the most recent message
                self._last_db = db
                last = [ln for ln in db.splitlines() if ln.strip()]
                if last:
                    self._add_message("user", last[-1])
            # update mic button label and assistant status label
            mic = GetMicrophoneStatus()
            self.mic_btn.config(text="Stop Mic" if mic=="True" else "Start Mic")
            self.status_label.config(text=GetAssistantStatus())
        except Exception as e:
            print("[GUI] poll error:", e)
        finally:
            self.after(self.POLL_INTERVAL, self._poll_files)

    # UI actions
    def _on_send(self, event=None):
        txt = self.entry_var.get().strip()
        if not txt:
            return
        # write into Database.data (same contract as original GUI)
        write_file(DB_FILE, txt + "\n")
        append_chatlog("user", txt)
        # immediately show user's bubble
        self._add_message("user", txt)
        # clear input
        self.entry_var.set("")
        # hint assistant to process: write a short status
        SetAssistantStatus("Thinking ...")
        # Show immediate placeholder in Responses.data if you want
        write_file(RESP_FILE, "...")
        # update last trackers
        self._last_db = txt
        self._last_resp = "..."
        self.chat_canvas.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)

    def _toggle_mic(self):
        s = GetMicrophoneStatus()
        if s == "True":
            SetMicrophoneStatus("False")
            self.mic_btn.config(text="Start Mic")
        else:
            SetMicrophoneStatus("True")
            self.mic_btn.config(text="Stop Mic")

# ---- Public entrypoint expected by Main.py ----
def GraphicalUserInterface():
    # block until GUI exits
    app = ChatGUI()
    app.mainloop()

# Exported names used by Main.py
__all__ = [
    "GraphicalUserInterface",
    "SetAssistantStatus",
    "ShowTextToScreen",
    "TempDirectoryPath",
    "SetMicrophoneStatus",
    "AnswerModifier",
    "QueryModifier",
    "GetMicrophoneStatus",
    "GetAssistantStatus"
]
