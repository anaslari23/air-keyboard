import cv2
import numpy as np

class Button:
    def __init__(self, pos, text, size=[85, 85]):
        self.pos = pos
        self.size = size
        self.text = text

class KeyboardLayout:
    def __init__(self):
        self.keys = [
            ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
            ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
            ["A", "S", "D", "F", "G", "H", "J", "K", "L", ";"],
            ["Z", "X", "C", "V", "B", "N", "M", ",", ".", "/"]
        ]
        self.button_list = []
        self.create_buttons()

    def create_buttons(self):
        self.button_list = []
        # Standard Grid
        # Starting Y at 50, X at 50. 
        # Keys are 85x85, gap is 15. Total step 100.
        
        for i in range(len(self.keys)):
            for j, key in enumerate(self.keys[i]):
                self.button_list.append(Button([100 * j + 50, 100 * i + 50], key))
        
        # Modifier Row (Y = 450)
        # Shift, Space, Backspace, Enter
        # Total width approx 1000px (10 keys * 100)
        
        # Shift: Left side
        self.button_list.append(Button([50, 450], "SHIFT", [185, 85]))
        
        # Space: Center
        self.button_list.append(Button([250, 450], "SPACE", [485, 85]))
        
        # Backspace
        self.button_list.append(Button([750, 450], "BACK", [135, 85]))
        
        # Enter
        self.button_list.append(Button([900, 450], "ENTER", [135, 85]))

    def draw_keyboard(self, img, hovered_button=None, clicked_button=None):
        # High-Tech Style Configuration
        color_base = (40, 40, 40)       # Darker Gray
        color_border = (255, 200, 0)    # Cyan/Teal mix (BGR) -> actually let's go Cyan (255, 255, 0)
        color_text = (255, 255, 255)    # White
        color_hover = (255, 0, 255)     # Magenta
        color_click = (0, 255, 0)       # Green
        
        # Create overlay for transparency
        overlay = img.copy()
        
        # Draw Background Panel (HUD style)
        cv2.rectangle(overlay, (25, 25), (1085, 560), (0, 0, 0), cv2.FILLED)
        
        # Apply transparency to background
        alpha = 0.7 # Darker background for better contrast
        img = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)

        for button in self.button_list:
            x, y = button.pos
            w, h = button.size
            
            # Determine colors based on state
            current_border = color_border
            current_fill = color_base
            current_text = color_text
            
            if button == clicked_button:
                current_border = color_click
                current_fill = (0, 150, 0) 
                current_text = (0, 0, 0)
            elif button == hovered_button:
                current_border = color_hover
                current_fill = (80, 0, 80) 
            
            # Draw Button Fill (Rounded effect by drawing filled rect slightly smaller + circles? 
            # OpenCV doesn't have native rounded rect. Let's stick to clean rects but with "corner cuts" for sci-fi look)
            
            # Sci-Fi "Cut Corner" Box
            cut_len = 15
            pts = np.array([
                [x + cut_len, y],
                [x + w - cut_len, y],
                [x + w, y + cut_len],
                [x + w, y + h - cut_len],
                [x + w - cut_len, y + h],
                [x + cut_len, y + h],
                [x, y + h - cut_len],
                [x, y + cut_len]
            ], np.int32)
            pts = pts.reshape((-1, 1, 2))
            
            cv2.fillPoly(img, [pts], current_fill)
            cv2.polylines(img, [pts], True, current_border, 2)

            # Draw Text
            font_scale = 2
            thickness = 2
            if len(button.text) > 1: 
                font_scale = 1.5
                thickness = 2
            
            text_size = cv2.getTextSize(button.text, cv2.FONT_HERSHEY_PLAIN, font_scale, thickness)[0]
            text_x = x + (w - text_size[0]) // 2
            text_y = y + (h + text_size[1]) // 2
            
            cv2.putText(img, button.text, (text_x, text_y),
                        cv2.FONT_HERSHEY_PLAIN, font_scale, current_text, thickness)
            
        return img
