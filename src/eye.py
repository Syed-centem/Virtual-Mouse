import cv2
import dlib
import numpy as np
import pyautogui
import time

# --- CONFIGURATION (TUNE THESE) ---
# Lower = Slower/Smoother. Higher = Faster/Jittery. Try 1.5 to 2.5
MOUSE_SENSITIVITY = 1.5  

# Higher = Easier to click (but might blink accidentally). Try 0.19 to 0.25
BLINK_THRESHOLD = 0.20   

# Seconds to wait between clicks (prevents double-clicking)
BLINK_COOLDOWN = 0.5     

# 0.1 to 1.0. Lower = Smoother but laggy. Higher = Responsive but jittery.
SMOOTHING_FACTOR = 0.5   
# ----------------------------------

pyautogui.FAILSAFE = False  
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

cap = cv2.VideoCapture(0)
screen_w, screen_h = pyautogui.size()

# Global variables for smoothing
prev_x, prev_y = pyautogui.position()

def eye_aspect_ratio(eye):
    vertical1 = np.linalg.norm(eye[1] - eye[5])
    vertical2 = np.linalg.norm(eye[2] - eye[4])
    horizontal = np.linalg.norm(eye[0] - eye[3])
    return (vertical1 + vertical2) / (2.0 * horizontal)

def calibrate():
    print("Starting Auto-Calibration...")
    start_time = time.time()
    countdown_duration = 3
    calibration_readings = [] 

    while True:
        ret, frame = cap.read()
        if not ret: continue
        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector(gray)
        
        elapsed = time.time() - start_time
        remaining = countdown_duration - elapsed

        if remaining > 0:
            text = f"Hold Still: {int(remaining) + 1}"
            color = (0, 255, 255)
            if remaining < 1.0:
                text = "Calibrating..."
                color = (0, 255, 0)
                if faces:
                    landmarks = predictor(gray, faces[0])
                    calibration_readings.append((landmarks.part(33).x, landmarks.part(33).y))

            cv2.putText(frame, text, (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.5, color, 3)
            h, w, _ = frame.shape
            cv2.rectangle(frame, (w//2 - 20, h//2 - 20), (w//2 + 20, h//2 + 20), (255, 255, 255), 2)
            cv2.imshow('Eye Controlled Mouse', frame)
            cv2.waitKey(1)
        else:
            if len(calibration_readings) > 0:
                readings = np.array(calibration_readings)
                avg_x = np.mean(readings[:, 0])
                avg_y = np.mean(readings[:, 1])
                print(f"✅ Calibration Complete. Center: ({avg_x:.1f}, {avg_y:.1f})")
                return (avg_x, avg_y)
            else:
                print("❌ Face not detected. Defaulting to center.")
                h, w, _ = frame.shape
                return (w // 2, h // 2)
    return None

calibration_data = calibrate()

last_left_click = 0
last_right_click = 0
last_double_click = 0

if calibration_data:
    try:
        while True:
            ret, frame = cap.read()
            if not ret: break
            frame = cv2.flip(frame, 1)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = detector(gray)

            for face in faces:
                landmarks = predictor(gray, face)
                
                # --- 1. Calculate Target Position ---
                nose_x = landmarks.part(33).x
                nose_y = landmarks.part(33).y
                
                diff_x = (nose_x - calibration_data[0]) * MOUSE_SENSITIVITY
                diff_y = (nose_y - calibration_data[1]) * MOUSE_SENSITIVITY

                target_x = np.clip(screen_w/2 + diff_x * 5, 0, screen_w - 1) # *5 maps small head movement to big screen
                target_y = np.clip(screen_h/2 + diff_y * 5, 0, screen_h - 1)

                # --- 2. Smoothing (Low Pass Filter) ---
                # Instead of jumping to target, move 50% of the way there
                smooth_x = prev_x + (target_x - prev_x) * SMOOTHING_FACTOR
                smooth_y = prev_y + (target_y - prev_y) * SMOOTHING_FACTOR
                
                pyautogui.moveTo(smooth_x, smooth_y)
                prev_x, prev_y = smooth_x, smooth_y

                # --- 3. Blink Detection ---
                left_eye = np.array([(landmarks.part(i).x, landmarks.part(i).y) for i in range(36, 42)])
                right_eye = np.array([(landmarks.part(i).x, landmarks.part(i).y) for i in range(42, 48)])
                
                left_ear = eye_aspect_ratio(left_eye)
                right_ear = eye_aspect_ratio(right_eye)
                
                # Optional: Print EAR values to debug (Uncomment to see your values)
                # print(f"Left: {left_ear:.2f} | Right: {right_ear:.2f}")

                current_time = time.time()

                # Left Click
                if left_ear < BLINK_THRESHOLD and right_ear > BLINK_THRESHOLD:
                    if current_time - last_left_click > BLINK_COOLDOWN:
                        pyautogui.click(button='left')
                        last_left_click = current_time
                        print("✅ Left Click")

                # Right Click
                if right_ear < BLINK_THRESHOLD and left_ear > BLINK_THRESHOLD:
                    if current_time - last_right_click > BLINK_COOLDOWN:
                        pyautogui.click(button='right')
                        last_right_click = current_time
                        print("✅ Right Click")

                # Double Click
                if left_ear < BLINK_THRESHOLD and right_ear < BLINK_THRESHOLD:
                    if current_time - last_double_click > BLINK_COOLDOWN:
                        pyautogui.doubleClick()
                        last_double_click = current_time
                        print("✅ Double Click")

            cv2.imshow('Eye Controlled Mouse', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    except KeyboardInterrupt:
        pass

    cap.release()
    cv2.destroyAllWindows()
