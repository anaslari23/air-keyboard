import cv2
import numpy as np
import pyperclip

class EmojiButton:
    def __init__(self, pos, emoji, size=[60, 60]):
        self.pos = pos
        self.size = size
        self.emoji = emoji

class EmojiPanel:
    def __init__(self):
        # Common emojis
        self.emojis = [
            "😀", "😂", "🤣", "😊", "😍",
            "🥰", "😎", "🤔", "😮", "😢",
            "😭", "😡", "👍", "👎", "👏",
            "🙏", "💪", "✌️", "🤝", "❤️",
            "🔥", "✨", "⭐", "💯", "✅",
            "❌", "⚠️", "🎉", "🎊", "🎈"
        ]
        
        # Special characters
        self.special_chars = [
            "@", "#", "$", "%", "^",
            "&", "*", "(", ")", "-",
            "_", "=", "+", "[", "]",
            "{", "}", "|", "\\", ":",
            ";", "'", '"', "<", ">",
            ",", ".", "?", "/", "~"
        ]
        
        self.button_list = []
        self.special_button_list = []
        self.create_buttons()
        
        self.show_emojis = True  # Toggle between emoji/special chars
        
    def create_buttons(self):
        # Create emoji buttons (6x5 grid)
        for i in range(5):
            for j in range(6):
                idx = i * 6 + j
                if idx < len(self.emojis):
                    self.button_list.append(
                        EmojiButton([100 + j * 70, 100 + i * 70], self.emojis[idx])
                    )
        
        # Create special char buttons (6x5 grid)
        for i in range(5):
            for j in range(6):
                idx = i * 6 + j
                if idx < len(self.special_chars):
                    self.special_button_list.append(
                        EmojiButton([100 + j * 70, 100 + i * 70], self.special_chars[idx])
                    )
    
    def draw_panel(self, img, hovered_button=None, clicked_button=None):
        # Background
        overlay = img.copy()
        cv2.rectangle(overlay, (50, 50), (550, 450), (0, 0, 0), cv2.FILLED)
        alpha = 0.85
        img = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)
        
        # Title
        title = "EMOJIS" if self.show_emojis else "SPECIAL"
        cv2.putText(img, title, (220, 80), cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 0), 2)
        
        # Toggle button
        cv2.rectangle(img, (450, 55), (540, 85), (100, 100, 100), cv2.FILLED)
        cv2.putText(img, "SWITCH", (455, 75), cv2.FONT_HERSHEY_PLAIN, 1.5, (255, 255, 255), 1)
        
        # Draw buttons
        buttons = self.button_list if self.show_emojis else self.special_button_list
        
        for button in buttons:
            x, y = button.pos
            w, h = button.size
            
            color = (80, 80, 80)
            if button == clicked_button:
                color = (0, 255, 0)
            elif button == hovered_button:
                color = (150, 0, 150)
            
            cv2.rectangle(img, (x, y), (x + w, y + h), color, cv2.FILLED)
            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 200, 0), 2)
            
            # Draw emoji/char (using text)
            cv2.putText(img, button.emoji, (x + 15, y + 40),
                       cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 255), 2)
        
        return img
    
    def check_click(self, x, y):
        """Check if position clicks a button. Returns emoji/char or None."""
        # Check toggle button
        if 450 < x < 540 and 55 < y < 85:
            self.show_emojis = not self.show_emojis
            return None
        
        buttons = self.button_list if self.show_emojis else self.special_button_list
        
        for button in buttons:
            bx, by = button.pos
            bw, bh = button.size
            if bx < x < bx + bw and by < y < by + bh:
                # Copy to clipboard
                pyperclip.copy(button.emoji)
                return button.emoji
        
        return None
    
    def get_hovered_button(self, x, y):
        """Get button under cursor."""
        buttons = self.button_list if self.show_emojis else self.special_button_list
        
        for button in buttons:
            bx, by = button.pos
            bw, bh = button.size
            if bx < x < bx + bw and by < y < by + bh:
                return button
        
        return None
