# Main.py — Aesthetic Light Mode Upgrade
import customtkinter as ctk
import threading
import re
import sys
import time
from Backend.GeminiBrain import bot
from Backend.SpeechToText import SpeechRecognition
from Backend.TextToSpeech import TextToSpeech
from Backend.Automation import Automation

# --- Configuration ---
ctk.set_appearance_mode("Light")  # <--- SWITCHED TO LIGHT MODE
ctk.set_default_color_theme("blue")

# --- New "Clean & Light" Color Palette ---
COLORS = {
    "bg": "#f0f2f5",           # Soft Light Gray (Main Background)
    "sidebar": "#ffffff",      # Pure White (Sidebar)
    "chat_bg": "#f0f2f5",      # Chat Area Matches Background
    "user_bubble": "#2563eb",  # Vibrant Blue
    "bot_bubble": "#ffffff",   # White Card for Bot
    "input_bg": "#ffffff",     # White Input Bar
    "text": "#111827",         # Dark Charcoal (Primary Text)
    "text_dim": "#6b7280",     # Medium Gray (Secondary Text)
    "accent": "#3b82f6",       # Bright Blue Accent
    "danger": "#ef4444",       # Red (Mic Active)
    "success": "#10b981",      # Green (Online)
    "border": "#e5e7eb"        # Subtle Borders
}

# --- Helper to remove Markdown ---
def clean_markdown(text):
    if not text: return ""
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text) 
    text = re.sub(r'#{1,6}\s?', '', text)        
    text = re.sub(r'\*(.*?)\*', r'\1', text)     
    text = re.sub(r'`(.*?)`', r'\1', text)       
    return text.strip()

class AestheticApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Proton AI")
        self.geometry("1100x750")
        self.configure(fg_color=COLORS["bg"])
        
        # Grid Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- 1. Sidebar (Left) ---
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=COLORS["sidebar"])
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1) 

        # Logo
        self.logo = ctk.CTkLabel(self.sidebar, text="PROTON", font=("Segoe UI", 28, "bold"), text_color=COLORS["text"])
        self.logo.grid(row=0, column=0, padx=20, pady=(40, 10), sticky="w")
        
        self.subtitle = ctk.CTkLabel(self.sidebar, text="Virtual Assistant", font=("Segoe UI", 12), text_color=COLORS["text_dim"])
        self.subtitle.grid(row=1, column=0, padx=20, pady=(0, 30), sticky="w")

        # Mic Button (Outlined Style)
        self.mic_btn = ctk.CTkButton(
            self.sidebar, 
            text="🎤 Start Mic", 
            font=("Segoe UI", 14, "bold"),
            fg_color=COLORS["bg"], 
            text_color=COLORS["text"],
            hover_color="#e2e8f0",
            height=50, 
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
            command=self.toggle_mic
        )
        self.mic_btn.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        # Status
        self.status_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.status_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        self.status_dot = ctk.CTkLabel(self.status_frame, text="●", font=("Arial", 18), text_color=COLORS["success"])
        self.status_dot.pack(side="left", padx=(0, 5))
        self.status_text = ctk.CTkLabel(self.status_frame, text="Online", font=("Segoe UI", 13), text_color=COLORS["text_dim"])
        self.status_text.pack(side="left")

        # Footer
        self.footer = ctk.CTkLabel(self.sidebar, text="v3.0 • Gemini Powered", font=("Segoe UI", 10), text_color=COLORS["text_dim"])
        self.footer.grid(row=5, column=0, padx=20, pady=20, sticky="w")

        # --- 2. Main Chat Area (Right) ---
        self.chat_area = ctk.CTkScrollableFrame(
            self, 
            fg_color=COLORS["chat_bg"], 
            corner_radius=0
        )
        self.chat_area.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)

        # --- 3. Input Area (Bottom) ---
        self.input_container = ctk.CTkFrame(self, fg_color=COLORS["bg"], height=80, corner_radius=0)
        self.input_container.grid(row=1, column=1, sticky="ew")
        
        # White Pill-Shape Background for Input
        self.input_bg = ctk.CTkFrame(self.input_container, fg_color=COLORS["input_bg"], corner_radius=30, border_width=1, border_color=COLORS["border"])
        self.input_bg.pack(fill="x", expand=True, padx=30, pady=20)

        self.entry = ctk.CTkEntry(
            self.input_bg, 
            placeholder_text="Type a message to Proton...", 
            border_width=0, 
            fg_color="transparent", 
            height=50, 
            font=("Segoe UI", 14),
            text_color=COLORS["text"],
            placeholder_text_color=COLORS["text_dim"]
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(20, 10))
        self.entry.bind("<Return>", self.send_text)

        self.send_btn = ctk.CTkButton(
            self.input_bg, 
            text="➤", 
            width=50, 
            height=40, 
            fg_color=COLORS["accent"], 
            hover_color="#1d4ed8",
            corner_radius=20,
            font=("Arial", 18),
            text_color="white",
            command=self.send_text
        )
        self.send_btn.pack(side="right", padx=(0, 10), pady=5)

        # Logic
        self.mic_on = False
        self.add_message("System", "Welcome back! How can I help you today?")

    def add_message(self, sender, text):
        clean_text_str = clean_markdown(text)
        
        if sender == "User":
            align_frame = "e"
            bubble_color = COLORS["user_bubble"]
            text_color = "#ffffff"
            margin = (50, 10)
        elif sender == "Bot":
            align_frame = "w"
            bubble_color = COLORS["bot_bubble"]
            text_color = COLORS["text"]
            margin = (10, 50)
        else: # System
            align_frame = "center"
            bubble_color = "transparent"
            text_color = COLORS["text_dim"]
            margin = (10, 10)

        msg_frame = ctk.CTkFrame(self.chat_area, fg_color="transparent")
        msg_frame.pack(anchor=align_frame, pady=5, padx=margin, fill="x")

        bubble = ctk.CTkLabel(
            msg_frame, 
            text=clean_text_str, 
            fg_color=bubble_color, 
            corner_radius=18,
            wraplength=600,
            font=("Segoe UI", 15),
            text_color=text_color,
            padx=15, pady=10,
            justify="left"
        )
        
        if sender == "System":
            bubble.configure(font=("Segoe UI", 12, "italic"))
        
        bubble.pack(anchor=align_frame)
        
        self.update_idletasks()
        self.chat_area._parent_canvas.yview_moveto(1.0)

    def update_status(self, status_msg, color_key="success"):
        self.status_text.configure(text=status_msg)
        self.status_dot.configure(text_color=COLORS.get(color_key, COLORS["success"]))

    def send_text(self, event=None):
        text = self.entry.get()
        if not text: return
        self.entry.delete(0, "end")
        
        self.add_message("User", text)
        threading.Thread(target=self.process_backend, args=(text,), daemon=True).start()

    def process_backend(self, text):
        self.update_status("Thinking...", "accent")
        try:
            response = bot.send_message(text)
            
            if "COMMAND:" in response:
                parts = response.split(":")
                action = parts[1]
                target = parts[2]
                
                if action == "EXIT":
                    self.add_message("Bot", "Goodbye! 👋 Shutting down...")
                    TextToSpeech("Goodbye!")
                    self.after(2000, self.destroy)
                    return

                self.update_status(f"Action: {action}", "accent")
                Automation([f"{action} {target}"])
                final_reply = f"✅ I have {action.lower()}ed {target}."
            else:
                final_reply = response

            self.add_message("Bot", final_reply)
            TextToSpeech(clean_markdown(final_reply))
            
        except Exception as e:
            self.add_message("System", f"Error: {e}")
        finally:
            self.update_status("Online", "success")

    def toggle_mic(self):
        self.mic_on = not self.mic_on
        if self.mic_on:
            self.mic_btn.configure(text="● Listening...", fg_color=COLORS["danger"], text_color="white", hover_color="#b91c1c")
            self.update_status("Listening...", "danger")
            threading.Thread(target=self.mic_loop, daemon=True).start()
        else:
            self.mic_btn.configure(text="🎤 Start Mic", fg_color=COLORS["bg"], text_color=COLORS["text"], hover_color="#e2e8f0")
            self.update_status("Online", "success")

    def mic_loop(self):
        while self.mic_on:
            try:
                text = SpeechRecognition()
                if text:
                    self.entry.insert(0, text)
                    self.send_text()
            except: break

if __name__ == "__main__":
    app = AestheticApp()
    app.mainloop()