import tkinter as tk
from PIL import Image, ImageTk, ImageSequence
import subprocess
import sys

# -------------------------
# Run Files in Subprocess
# -------------------------
def run_file(file_name):
    try:
        subprocess.Popen([sys.executable, file_name], shell=True)
    except Exception as e:
        print(f"Error running {file_name}: {e}")

def exit_launcher():
    root.destroy()
    sys.exit(0)

# -------------------------
# Splash Screen
# -------------------------
def show_splash():
    splash = tk.Toplevel()
    splash.title("Welcome")
    splash.geometry("650x400+450+200")
    splash.config(bg="#0f172a")

    try:
        img = Image.open("purple-gradient.jpg")
        img = img.resize((650, 400))
        bg_img = ImageTk.PhotoImage(img)

        bg_label = tk.Label(splash, image=bg_img)
        bg_label.image = bg_img
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
    except Exception as e:
        print(f"Could not load splash image: {e}")

    title = tk.Label(
        splash,
        text="Virtual Mouse Using Hand & Eye Gesture\nwith Chatbot",
        font=("Arial", 16, "bold"),
        bg="#0f172a",
        fg="cyan",
        justify="center"
    )
    title.pack(pady=40)

    credits = tk.Label(
        splash,
        text="🎯 Final Year Project\n\nDeveloped by: Syed Junaid Hussain\nUnder Guidance of: Sirisha M",
        font=("Arial", 12),
        bg="#0f172a",
        fg="white",
        justify="center"
    )
    credits.pack(pady=20)

    footer = tk.Label(
        splash,
        text="Launching Project...",
        font=("Arial", 10, "italic"),
        bg="#0f172a",
        fg="orange"
    )
    footer.pack(side="bottom", pady=20)

    splash.after(3500, splash.destroy)

# -------------------------
# Show Features with Clickable GIFs
# -------------------------
def show_features():
    features = {
        "Gesture Recognition": [
            ("Neutral Gesture", "l.gif"),
            ("Move Cursor", "m.gif"),
            ("Left Click", "n.gif"),
            ("Right Click", "o.gif"),
            ("Double Click", "p.gif"),
            ("Scrolling", "q.gif"),
            ("Drag and Drop", "r.gif"),
            ("Volume Control", "s.gif"),
            ("Brightness Control", "t.gif"),
            ("Multiple item selection","u.gif")
        ],
        "Voice Assistant (Proton)": [
            ("Google Search", "a.gif"),
            ("Find Location", "b.gif"),
            ("File Navigation", "c.gif"),
            ("Current Date/Time", "d.gif"),
            ("Copy", "e.gif"),
            ("Sleep/Wake up", "f.gif"),
            ("Exit", "g.gif"),
            ("Go back","h.gif"),
            ("Launch gesture recognition","i.gif"),
            ("Open","j.gif"),
            ("Paste","k.gif")
        ]
    }

    feat_window = tk.Toplevel()
    feat_window.title("Project Features")
    feat_window.geometry("900x700")
    feat_window.config(bg="#0f172a")

    title = tk.Label(feat_window, text="Click on command to view demonstration",
                     font=("Arial", 16, "bold"), bg="#0f172a", fg="cyan")
    title.pack(pady=20)

    gif_display = tk.Label(feat_window, bg="#0f172a")
    gif_display.pack(pady=10)

    current_animation = None  # keep track of running GIF animation

    def show_gif(gif_path):
        nonlocal current_animation

        # Cancel previous animation if any
        if current_animation is not None:
            feat_window.after_cancel(current_animation)
            current_animation = None

        try:
            gif_img = Image.open(gif_path)
            frames = [ImageTk.PhotoImage(frame.copy().resize((300, 300))) for frame in ImageSequence.Iterator(gif_img)]

            def animate(idx=0):
                nonlocal current_animation
                gif_display.config(image=frames[idx])
                idx = (idx + 1) % len(frames)
                current_animation = feat_window.after(100, animate, idx)

            animate()
        except Exception as e:
            print(f"Could not load GIF {gif_path}: {e}")

    # Stop GIF Button
    def stop_gif():
        nonlocal current_animation
        if current_animation is not None:
            feat_window.after_cancel(current_animation)
            current_animation = None
            gif_display.config(image="")  # clear GIF display

    stop_btn = tk.Button(feat_window, text="Stop GIF", font=("Arial", 11, "bold"),
                         bg="red", fg="white", command=stop_gif)
    stop_btn.pack(pady=5)

    # Feature Buttons
    for category, items in features.items():
        frame = tk.LabelFrame(feat_window, text=category, font=("Arial", 12, "bold"),
                              bg="#0f172a", fg="cyan", padx=10, pady=10)
        frame.pack(fill="x", padx=20, pady=10)

        for command, gif_path in items:
            cmd_btn = tk.Button(frame, text=command, font=("Arial", 11, "bold"),
                                bg="#1e293b", fg="white",
                                command=lambda path=gif_path: show_gif(path))
            cmd_btn.pack(fill="x", padx=5, pady=3)

# -------------------------
# Main Launcher
# -------------------------
def show_launcher():
    global root
    root.deiconify()
    root.title("Virtual Mouse Using Hand & Eye Gesture with Chatbot")
    root.geometry("720x780")
    root.config(bg="#0f172a")

    title = tk.Label(
        root,
        text="Virtual Mouse Using Hand & Eye Gesture with Chatbot",
        font=("Arial", 18, "bold"),
        bg="#0f172a",
        fg="cyan"
    )
    title.pack(pady=15)
    # Aim
    aim = tk.Label(
        root,
        text=(
            "🎯 Aim: To develop an intelligent virtual mouse system that allows\n"
            "users to control the computer using hand gestures and eye blinks,\n"
            "integrated with a chatbot for seamless interaction."
        ),
        font=("Arial", 12),
        bg="#0f172a",
        fg="lightgray",
        justify="center"
    )
    aim.pack(pady=10)


    info = tk.Label(
        root,
        text="📌 Choose a module to run:",
        font=("Arial", 13, "bold"),
        bg="#0f172a",
        fg="white"
    )
    info.pack(pady=8)

    options = [
        ("🖐 Hand Gesture Mouse (Laptop Camera)", "gestcon.py"),
        ("👁 Eye Gesture Mouse (Laptop Camera)", "eye.py"),
        ("🎙 Voice Assistant(Chatbot)", "Main.py"),
    ]

    for text, file_name in options:
        btn = tk.Button(
            root,
            text=text,
            width=60,
            height=2,
            bg="#2563eb",
            fg="white",
            font=("Arial", 11, "bold"),
            command=lambda f=file_name: run_file(f)
        )
        btn.pack(pady=5)

    # Features Button
    features_btn = tk.Button(
        root,
        text="📄 View Features",
        width=60,
        height=2,
        bg="#10b981",
        fg="white",
        font=("Arial", 11, "bold"),
        command=show_features
    )
    features_btn.pack(pady=5)

    # Exit Button
    exit_btn = tk.Button(
        root,
        text="❌ Exit Launcher",
        width=60,
        height=2,
        bg="red",
        fg="white",
        font=("Arial", 11, "bold"),
        command=exit_launcher
    )
    exit_btn.pack(pady=20)

# -------------------------
# Launch Flow
# -------------------------
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # hide main window during splash

    show_splash()
    root.after(3600, show_launcher)
    root.mainloop()
