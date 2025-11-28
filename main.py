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
from hand_tracker import HandTracker
from keyboard_layout import KeyboardLayout

# Initialize Keyboard Controller
controller = Controller()

def main():
    print("Starting Air Keyboard V2... Press 'q' to quit.")
    # Initialize Camera
    cap = cv2.VideoCapture(0)
    cap.set(3, 1280) # Width
    cap.set(4, 720)  # Height

    # Initialize Hand Tracker
    tracker = HandTracker(detection_confidence=0.8)

    # Initialize Keyboard Layout
    keyboard = KeyboardLayout()
    
    final_text = ""
    
    # Smoothing variables
    # Dictionary to store state for each hand: {hand_id: {'prev_x': 0, 'prev_y': 0, 'clicked': False, 'last_click_time': 0}}
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
        
        # We need to handle multiple hands. 
        # tracker.find_position only returns one hand's landmarks by default.
        # We need to access tracker.results.multi_hand_landmarks directly or modify tracker.
        # Let's modify the loop to iterate through detected hands using the tracker's results.
        
        hovered_button = None
        clicked_button = None
        
        # List to store cursor positions for drawing on top later
        cursors_to_draw = []
        
        if tracker.results.multi_hand_landmarks:
            for hand_idx, hand_lms in enumerate(tracker.results.multi_hand_landmarks):
                # Initialize state for new hands
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
                    # Index Tip (8) and Thumb Tip (4)
                    raw_x8, raw_y8 = lm_list[8][1], lm_list[8][2]
                    x4, y4 = lm_list[4][1], lm_list[4][2]
                    
                    # Smoothing
                    if state['prev_x'] == 0: state['prev_x'], state['prev_y'] = raw_x8, raw_y8
                    
                    curr_x = state['prev_x'] + (raw_x8 - state['prev_x']) / smoothing_factor
                    curr_y = state['prev_y'] + (raw_y8 - state['prev_y']) / smoothing_factor
                    
                    x8, y8 = int(curr_x), int(curr_y)
                    state['prev_x'], state['prev_y'] = curr_x, curr_y
                    
                    # Magnetic Key Logic
                    # Find closest key center
                    closest_button = None
                    min_dist = 10000
                    
                    for button in keyboard.button_list:
                        bx, by = button.pos
                        bw, bh = button.size
                        cx_key, cy_key = bx + bw // 2, by + bh // 2
                        
                        dist_to_key = math.hypot(x8 - cx_key, y8 - cy_key)
                        
                        # Magnetic threshold (snap if within 1.2x of key radius approx)
                        # Key is ~85x85, radius ~42. Let's say snap if < 60px from center
                        if dist_to_key < 60:
                            if dist_to_key < min_dist:
                                min_dist = dist_to_key
                                closest_button = button
                    
                    # If snapped, update cursor position visually to key center (optional, or just highlight)
                    # Let's just highlight and use it for clicking
                    if closest_button:
                        hovered_button = closest_button
                        # Optional: Snap cursor visually? 
                        # x8, y8 = closest_button.pos[0] + closest_button.size[0]//2, closest_button.pos[1] + closest_button.size[1]//2
                    
                    # Store cursor to draw later
                    cursors_to_draw.append((x8, y8))
                    
                    # Click Logic
                    if hovered_button:
                        button = hovered_button
                        
                        # Distance between fingers
                        length = math.hypot(x8 - x4, y8 - y4)
                        
                        current_time = time.time()
                        
                        if length < 30:
                            if not state['clicked'] and (current_time - state['last_click_time'] > 0.2):
                                clicked_button = button
                                state['clicked'] = True
                                state['last_click_time'] = current_time
                                
                                # Play Sound (Non-blocking)
                                os.system('afplay /System/Library/Sounds/Tink.aiff &')
                                
                                # Execute Key Press
                                try:
                                    if button.text == "SPACE":
                                        final_text += " "
                                        controller.press(Key.space)
                                        controller.release(Key.space)
                                    elif button.text == "ENTER":
                                        final_text += "\n"
                                        controller.press(Key.enter)
                                        controller.release(Key.enter)
                                    elif button.text == "BACK":
                                        final_text = final_text[:-1]
                                        controller.press(Key.backspace)
                                        controller.release(Key.backspace)
                                    elif button.text == "SHIFT":
                                        is_shift = not is_shift
                                    else:
                                        char_to_type = button.text
                                        if not is_shift:
                                            char_to_type = char_to_type.lower()
                                        final_text += char_to_type
                                        controller.press(char_to_type)
                                        controller.release(char_to_type)
                                except Exception as e:
                                    print(f"Error: {e}")
                                    
                        elif length > 40:
                            state['clicked'] = False

        # Draw Keyboard
        img = keyboard.draw_keyboard(img, hovered_button, clicked_button)
        
        # Draw Shift Status
        if is_shift:
             cv2.putText(img, "SHIFT ON", (1100, 100), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 255), 2)

        # Re-draw cursors on top of keyboard
        for cx, cy in cursors_to_draw:
             cv2.circle(img, (cx, cy), 8, (255, 0, 255), cv2.FILLED)

        # Display Output Text
        # High tech text box
        cv2.rectangle(img, (50, 600), (1230, 700), (0, 0, 0), cv2.FILLED)
        cv2.rectangle(img, (50, 600), (1230, 700), (255, 255, 0), 2) # Cyan border
        cv2.putText(img, final_text, (60, 675), cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 4)

        # Display
        cv2.imshow("Air Keyboard V2", img)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
