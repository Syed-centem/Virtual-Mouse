# **👁️ VISION: AI Virtual Mouse & Assistant**

- Vision is a comprehensive, multimodal Human-Computer Interaction (HCI) system designed to bridge the gap between physical peripherals and natural user behavior. It replaces the traditional mouse and keyboard with Hand Gestures, Eye Gaze, and Voice Commands, powered by a robust Generative AI backend for system automation.

## **🚀 Features**

**1. 👋 Virtual Mouse (Hand Gestures)**

- Control your cursor with precision using natural hand movements.

- Technology: Google MediaPipe Hands (21-point Landmark Detection).

- **Gestures:**

1) Move Cursor: Index Finger Up.

2) Left Click: Pinch (Thumb + Index).

3) Right Click: Victory Sign (Index + Middle).

4) Scroll: Pinky Finger Up.

5) Smoothing: Weighted Moving Average algorithm eliminates cursor jitter.

**2. 👁️ Virtual Mouse (Eye Tracking)**

- Hands-free navigation for complete accessibility.

- Technology: Dlib 68-Point Facial Landmark Predictor.

- **Functionality:**

1) Navigation: Head Pose Estimation (Nose Tip tracking).

2) Clicking: Eye Aspect Ratio (EAR) based blink detection.

3) Auto-Calibration: 3-second setup on launch to determine neutral head position.

**3. 🧠 AI Assistant (Gemini Brain)**

- An intelligent agent that understands context and controls the OS.

- Backend: Custom Raw HTTP Wrapper for Google Gemini 2.5 Flash.

- **Capabilities:**

1) Context-Aware Chat: Maintains conversation history.

2) System Automation: Opens apps (e.g., "Open Chrome"), checks time, and manages system processes.

3) Heuristic Routing: Local execution for system commands (<0.1s latency) vs. Cloud execution for complex reasoning.

**4. 🗣️ Voice Command & Automation**

- Smart Phonetic Correction: Automatically fixes common speech-to-text errors (e.g., "Start High" $\rightarrow$ "Start Eye").

- Process Orchestration: Manages system resources by automatically killing conflicting vision processes (e.g., stopping Hand Tracking before starting Eye Tracking).

## **🛠️ System Architecture**

- The project utilizes a Multi-Process, Event-Driven Architecture to ensure responsiveness.

1) **Frontend:** CustomTkinter (Modern Floating Dock UI).

2) **Vision Engine:** OpenCV, MediaPipe, Dlib.

3) **Intelligence:** Google Gemini API, SpeechRecognition.

4) **Automation:** PyAutoGUI, Psutil, Subprocess.


## **💻 Installation**

1) **Prerequisites**

- Python 3.8.10 (Recommended for MediaPipe stability).

- Visual Studio Build Tools (Required for Dlib).

- Webcam & Microphone.

2) **Setup Steps**

i) **Clone the Repository**

git clone 
cd Virtual-Mouse


ii) **Install Dependencies**

pip install -r requirements.txt


Note: If dlib fails, ensure CMake is installed (pip install cmake).

iii) **Configure Environment**
Create a .Env file in the root directory and add your API Key:


GOOGLE_API_KEY=AIzaSy...YourKeyHere


iV) **Run the Application**

python Main.py


## **🎮 Usage Guide**

**Voice Commands**

- "Start Hand": Activates Hand Gesture Mouse.

- "Start Eye": Activates Eye Tracking Mouse.

- "Stop": Stops all vision tracking.

**Gestures**

- Hand: Index Up to move, Pinch to click.

- Eye: Look to move cursor, Blink to click.

## **🔮 Future Scope**

[ ] **IoT Integration:** Control smart home devices via gestures.

[ ] **Offline LLM:** Integrate Llama-3 for privacy-focused, offline reasoning.

[ ] **Gaze Typing:** On-screen keyboard for paralyzed users.

## **👥 Contributors**

**SYED JUNAID HUSSAIN**

**MOHAMMED SUBHANI MUSHARRAF**
