# Backend/Automation.py — Debug Version
import os
import subprocess
import webbrowser
import psutil 
import sys
import time

# --- PATH CONFIGURATION ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
EYE_SCRIPT = os.path.join(PROJECT_ROOT, "Eye.py")
GESTURE_SCRIPT = os.path.join(PROJECT_ROOT, "gestcon.py")

# Common System Apps
sys_apps = {
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "cmd": "cmd.exe",
    "vscode": "code",
}

def kill_process_by_name(script_name):
    """Kills any running python process that contains script_name."""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                cmdline = proc.info['cmdline']
                if cmdline and any(script_name.lower() in arg.lower() for arg in cmdline):
                    print(f"[Automation] Killing {script_name} (PID: {proc.info['pid']})")
                    proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

def OpenApp(app_name):
    app_name = app_name.lower().strip()
    
    # 1. LAUNCH EYE TRACKING
    if "eye" in app_name or "vision" in app_name:
        print("[Automation] Stopping Hand Gesture to free camera...")
        kill_process_by_name("gestcon.py") 
        kill_process_by_name("Eye.py") 
        
        # Wait a moment for camera to release
        time.sleep(0.5)
        
        if os.path.exists(EYE_SCRIPT):
            print(f"[Automation] Launching {EYE_SCRIPT}...")
            subprocess.Popen([sys.executable, EYE_SCRIPT], cwd=PROJECT_ROOT)
            return True
        else:
            print(f"[ERROR] Eye.py not found at: {EYE_SCRIPT}")
            return False

    # 2. LAUNCH HAND GESTURES
    if "gesture" in app_name or "hand" in app_name:
        print("[Automation] Stopping Eye Tracking to free camera...")
        kill_process_by_name("Eye.py") 
        kill_process_by_name("gestcon.py")
        
        time.sleep(0.5)

        if os.path.exists(GESTURE_SCRIPT):
            print(f"[Automation] Launching {GESTURE_SCRIPT}...")
            subprocess.Popen([sys.executable, GESTURE_SCRIPT], cwd=PROJECT_ROOT)
            return True
        else:
            print(f"[ERROR] gestcon.py not found at: {GESTURE_SCRIPT}")
            return False

    # 3. SYSTEM APPS
    for key, path in sys_apps.items():
        if key in app_name:
            try:
                subprocess.Popen(path)
                return True
            except: pass
    
    # 4. WEB FALLBACK
    webbrowser.open(f"https://www.google.com/search?q={app_name}")
    return True

def CloseApp(app_name):
    app_name = app_name.lower().strip()
    if "eye" in app_name: return kill_process_by_name("Eye.py")
    if "gesture" in app_name or "hand" in app_name: return kill_process_by_name("gestcon.py")
    subprocess.call(f"taskkill /IM {app_name}.exe /F", shell=True)
    return True

def Automation(commands):
    for c in commands:
        # Fallback parsing if not formatted as COMMAND:OPEN:target
        if ":" in c:
            parts = c.split(":")
            target = parts[-1] # Get the last part as target
            cmd_type = parts[1] if len(parts) > 2 else "OPEN"
        else:
            target = c
            cmd_type = "OPEN"

        if "open" in c.lower() or "start" in c.lower(): OpenApp(target)
        elif "close" in c.lower() or "stop" in c.lower(): CloseApp(target)
        else: OpenApp(target)
    return True