import os
import warnings

# Suppress MediaPipe/TensorFlow logs
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
warnings.filterwarnings('ignore')

import cv2
import time
import math
import numpy as np
from pynput.keyboard import Controller, Key
from pynput.mouse import Controller as MouseController, Button
from hand_tracker import HandTracker
from keyboard_layout import KeyboardLayout
from emoji_panel import EmojiPanel

# Initialize Controllers
keyboard_controller = Controller()
mouse_controller = MouseController()

# Mode constants
MODE_KEYBOARD = 0
MODE_TRACKPAD = 1
MODE_EMOJI = 2

def main():
    print("Starting Air Keyboard V4... Press 'q' to quit.")
    # Initialize Camera
    cap = cv2.VideoCapture(0)
    cap.set(3, 1280) # Width
    cap.set(4, 720)  # Height

    # Initialize Hand Tracker
    tracker = HandTracker(detection_confidence=0.8)

    # Initialize Layouts
    keyboard = KeyboardLayout()
    emoji_panel = EmojiPanel()
    
    final_text = ""
    
    # Mode state
    current_mode = MODE_KEYBOARD
    mode_switch_start_time = None
    mode_switch_threshold = 2.0  # seconds
    
    # Smoothing variables
    hands_state = {}
    smoothing_factor = 2
    
    is_shift = False

    while True:
        success, img = cap.read()
        if not success:
            print("Error: Could not access the camera. Please check permissions.")
            break

        # Flip image for mirror view
        img = cv2.flip(img, 1)

        # Detect Hands
        img = tracker.find_hands(img, draw=True)
        
        hovered_button = None
        clicked_button = None
        cursors_to_draw = []
        
        # Mode Switching Logic: Detect open palm (all 5 fingers extended)
        if tracker.results.multi_hand_landmarks and len(tracker.results.multi_hand_landmarks) >= 1:
            # Check first hand for open palm gesture
            hand_lms = tracker.results.multi_hand_landmarks[0]
            h, w, c = img.shape
            
            # Get fingertips and bases
            thumb_tip = hand_lms.landmark[4]
            index_tip = hand_lms.landmark[8]
            middle_tip = hand_lms.landmark[12]
            ring_tip = hand_lms.landmark[16]
            pinky_tip = hand_lms.landmark[20]
            
            # Get palm base (wrist)
            wrist = hand_lms.landmark[0]
            
            # Check if all fingers are extended (tips are above bases)
            fingers_extended = (
                index_tip.y < hand_lms.landmark[6].y and  # Index
                middle_tip.y < hand_lms.landmark[10].y and  # Middle
                ring_tip.y < hand_lms.landmark[14].y and  # Ring
                pinky_tip.y < hand_lms.landmark[18].y  # Pinky
            )
            
            if fingers_extended:
                if mode_switch_start_time is None:
                    mode_switch_start_time = time.time()
                elif time.time() - mode_switch_start_time >= mode_switch_threshold:
                    # Switch mode
                    current_mode = (current_mode + 1) % 3
                    mode_switch_start_time = None
                    print(f"Switched to mode: {['KEYBOARD', 'TRACKPAD', 'EMOJI'][current_mode]}")
            else:
                mode_switch_start_time = None
        else:
            mode_switch_start_time = None
        
        # Draw mode switch progress indicator
        if mode_switch_start_time is not None:
            progress = min(1.0, (time.time() - mode_switch_start_time) / mode_switch_threshold)
            bar_width = int(200 * progress)
            cv2.rectangle(img, (540, 20), (740, 40), (50, 50, 50), cv2.FILLED)
            cv2.rectangle(img, (540, 20), (540 + bar_width, 40), (0, 255, 255), cv2.FILLED)
            cv2.putText(img, "SWITCHING MODE...", (545, 35), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)
        

        if tracker.results.multi_hand_landmarks:
            for hand_idx, hand_lms in enumerate(tracker.results.multi_hand_landmarks):
                if hand_idx not in hands_state:
                    hands_state[hand_idx] = {'prev_x': 0, 'prev_y': 0, 'clicked': False, 'last_click_time': 0}
                
                state = hands_state[hand_idx]
                
                # Get landmarks
                h, w, c = img.shape
                lm_list = []
                for id, lm in enumerate(hand_lms.landmark):
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    lm_list.append([id, cx, cy])
                
                if lm_list:
                    raw_x8, raw_y8 = lm_list[8][1], lm_list[8][2]
                    x4, y4 = lm_list[4][1], lm_list[4][2]
                    
                    # Smoothing
                    if state['prev_x'] == 0: state['prev_x'], state['prev_y'] = raw_x8, raw_y8
                    
                    curr_x = state['prev_x'] + (raw_x8 - state['prev_x']) / smoothing_factor
                    curr_y = state['prev_y'] + (raw_y8 - state['prev_y']) / smoothing_factor
                    
                    x8, y8 = int(curr_x), int(curr_y)
                    state['prev_x'], state['prev_y'] = curr_x, curr_y
                    
                    cursors_to_draw.append((x8, y8))
                    
                    # MODE-SPECIFIC LOGIC
                    if current_mode == MODE_KEYBOARD:
                        # Magnetic Key Logic
                        closest_button = None
                        min_dist = 10000
                        
                        for button in keyboard.button_list:
                            bx, by = button.pos
                            bw, bh = button.size
                            cx_key, cy_key = bx + bw // 2, by + bh // 2
                            dist_to_key = math.hypot(x8 - cx_key, y8 - cy_key)
                            
                            if dist_to_key < 60 and dist_to_key < min_dist:
                                min_dist = dist_to_key
                                closest_button = button
                        
                        if closest_button:
                            hovered_button = closest_button
                        
                        # Click Logic
                        if hovered_button:
                            button = hovered_button
                            length = math.hypot(x8 - x4, y8 - y4)
                            current_time = time.time()
                            
                            if length < 30:
                                if not state['clicked'] and (current_time - state['last_click_time'] > 0.2):
                                    clicked_button = button
                                    state['clicked'] = True
                                    state['last_click_time'] = current_time
                                    os.system('afplay /System/Library/Sounds/Tink.aiff &')
                                    
                                    try:
                                        if button.text == "SPACE":
                                            final_text += " "
                                            keyboard_controller.press(Key.space)
                                            keyboard_controller.release(Key.space)
                                        elif button.text == "ENTER":
                                            final_text += "\n"
                                            keyboard_controller.press(Key.enter)
                                            keyboard_controller.release(Key.enter)
                                        elif button.text == "BACK":
                                            final_text = final_text[:-1]
                                            keyboard_controller.press(Key.backspace)
                                            keyboard_controller.release(Key.backspace)
                                        elif button.text == "SHIFT":
                                            is_shift = not is_shift
                                        else:
                                            char_to_type = button.text
                                            if not is_shift:
                                                char_to_type = char_to_type.lower()
                                            final_text += char_to_type
                                            keyboard_controller.press(char_to_type)
                                            keyboard_controller.release(char_to_type)
                                    except Exception as e:
                                        print(f"Error: {e}")
                                        
                            elif length > 40:
                                state['clicked'] = False
                    
                    elif current_mode == MODE_TRACKPAD:
                        # Trackpad Mode: Control mouse cursor
                        # Map hand position to screen coordinates
                        screen_x = int(x8 * 1920 / 1280)  # Adjust to screen resolution
                        screen_y = int(y8 * 1080 / 720)
                        
                        mouse_controller.position = (screen_x, screen_y)
                        
                        # Click detection
                        length = math.hypot(x8 - x4, y8 - y4)
                        current_time = time.time()
                        
                        if length < 30:
                            if not state['clicked'] and (current_time - state['last_click_time'] > 0.2):
                                mouse_controller.click(Button.left)
                                state['clicked'] = True
                                state['last_click_time'] = current_time
                                os.system('afplay /System/Library/Sounds/Tink.aiff &')
                        elif length > 40:
                            state['clicked'] = False
                    
                    elif current_mode == MODE_EMOJI:
                        # Emoji Mode
                        emoji_hovered = emoji_panel.get_hovered_button(x8, y8)
                        if emoji_hovered:
                            hovered_button = emoji_hovered
                        
                        length = math.hypot(x8 - x4, y8 - y4)
                        current_time = time.time()
                        
                        if length < 30:
                            if not state['clicked'] and (current_time - state['last_click_time'] > 0.2):
                                result = emoji_panel.check_click(x8, y8)
                                if result:
                                    print(f"Copied to clipboard: {result}")
                                    final_text += result
                                state['clicked'] = True
                                state['last_click_time'] = current_time
                                os.system('afplay /System/Library/Sounds/Tink.aiff &')
                        elif length > 40:
                            state['clicked'] = False


        # Draw mode-specific UI
        if current_mode == MODE_KEYBOARD:
            img = keyboard.draw_keyboard(img, hovered_button, clicked_button)
            
            if is_shift:
                cv2.putText(img, "SHIFT ON", (1100, 100), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 255), 2)
            
            # Display Output Text
            cv2.rectangle(img, (50, 600), (1230, 700), (0, 0, 0), cv2.FILLED)
            cv2.rectangle(img, (50, 600), (1230, 700), (255, 255, 0), 2)
            cv2.putText(img, final_text[-50:], (60, 675), cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 4)
        
        elif current_mode == MODE_TRACKPAD:
            # Draw trackpad indicator
            cv2.rectangle(img, (50, 50), (350, 150), (0, 0, 0), cv2.FILLED)
            cv2.rectangle(img, (50, 50), (350, 150), (0, 255, 255), 2)
            cv2.putText(img, "TRACKPAD MODE", (60, 90), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 255), 2)
            cv2.putText(img, "Pinch to Click", (60, 120), cv2.FONT_HERSHEY_PLAIN, 1.5, (255, 255, 255), 1)
        
        elif current_mode == MODE_EMOJI:
            img = emoji_panel.draw_panel(img, hovered_button, clicked_button)
            
            # Show clipboard hint
            cv2.rectangle(img, (600, 50), (1100, 100), (0, 0, 0), cv2.FILLED)
            cv2.putText(img, "Copied: " + final_text[-10:], (610, 80), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)
        
        # Draw mode indicator
        mode_names = ["KEYBOARD", "TRACKPAD", "EMOJI"]
        mode_colors = [(255, 200, 0), (0, 255, 255), (255, 0, 255)]
        cv2.rectangle(img, (20, 20), (220, 60), (0, 0, 0), cv2.FILLED)
        cv2.rectangle(img, (20, 20), (220, 60), mode_colors[current_mode], 2)
        cv2.putText(img, mode_names[current_mode], (30, 50), cv2.FONT_HERSHEY_PLAIN, 2, mode_colors[current_mode], 2)
        
        # Re-draw cursors on top
        for cx, cy in cursors_to_draw:
            cv2.circle(img, (cx, cy), 8, (255, 0, 255), cv2.FILLED)

        # Display
        cv2.imshow("Air Keyboard V4", img)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
