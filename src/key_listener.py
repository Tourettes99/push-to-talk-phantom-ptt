import keyboard
from PyQt6.QtCore import QObject, pyqtSignal

class KeyListener(QObject):
    on_press = pyqtSignal()
    on_release = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.hotkey = None
        self.is_holding = False

    def set_hotkey(self, key_combination):
        """
        Sets the hotkey to listen for.
        Example: 'cntrl+alt+p' or 'num 0'
        """
        if self.hotkey:
            try:
                keyboard.remove_hotkey(self.handle_event)
            except:
                pass
                
        self.hotkey = key_combination
        # keyboard.hook is too broad, we want to check specifically for our key.
        # But for PTT we need press AND release. 
        # keyboard.add_hotkey usually triggers once on press. 
        # We need a hook that checks state.
        
        # New approach: Use keyboard.hook and filter for the specific key scan codes 
        # or names if we want robust PTT (hold down).
        # Simpler approach for "Combo":
        # keyboard.is_pressed(key) checks current state, but we need events.
        
        # Let's try hooking specific key.
        keyboard.hook_key(key_combination, self.handle_event, suppress=False)

    def handle_event(self, event):
        """
        Event handler for the specific key.
        """
        # This hook might be for a single key. If it's a combo, handle differently.
        # If the user wants a COMBINATION (Ctrl+Shift), `keyboard` handles that nicely with add_hotkey 
        # but release detection is tricky for combos.
        # USER REQUEST: "setup any numpad / numbers and a valid key from the keyboard in a combo"
        # Since exact PTT logic with complex combos on release is hard, 
        # I'll implement a logic that checks `keyboard.is_pressed(combo)` in a loop OR 
        # uses `keyboard.add_hotkey(..., callback, args=('down'))` and `('up')`.
        # Unfortunately keyboard mainly supports 'trigger'.
        
        # Better approach for PTT: 
        # Use `keyboard.hook(callback)` and check if the event matches the target combo.
        pass

# Re-implemeting with a simpler logic for PTT:
# We will let the user define a SINGLE trigger key for PTT (like 'v', 'num_0', 'mouse5'?) 
# The prompt says "setup any numpad / numbers and a valid key from the keyboard in a combo".
# This implies customized complex hotkeys.
# I will implement a Listener that accepts a key string, and detects down/up.

class PTTListener(QObject):
    pressed = pyqtSignal()
    released = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.target_hotkey = None
        self.trigger_key = None
        self.modifiers = []
        self.active = False
        self._hook = None

    def start_listening(self, hotkey_str):
        self.stop_listening()
        self.target_hotkey = hotkey_str
        
        if hotkey_str:
            try:
                # Parse the key combo
                # precise handling for "ctrl+shift+v" -> modifiers=['ctrl', 'shift'], trigger='v'
                parts = hotkey_str.lower().split('+')
                self.trigger_key = parts[-1].strip()
                self.modifiers = [m.strip() for m in parts[:-1]]
                
                # We hook ONLY the trigger key with suppression.
                # This prevents "5" from typing if "5" is the trigger.
                # For "ctrl+5", "5" is suppressed.
                self._hook = keyboard.hook_key(self.trigger_key, self._on_key_event, suppress=True)
            except Exception as e:
                print(f"Error hooking key: {e}")
                # Fallback? If hooking fails (e.g. bad key name), we can't do much.
                pass

    def stop_listening(self):
        if self._hook:
            keyboard.unhook(self._hook)
            self._hook = None
        self.active = False
            
    def _on_key_event(self, event):
        # Event handler for the specific (suppressed) trigger key
        
        # Check modifiers
        # validation: all modifiers must be pressed
        modifiers_ok = True
        for mod in self.modifiers:
            if not keyboard.is_pressed(mod):
                modifiers_ok = False
                break
        
        if event.event_type == 'down':
            if modifiers_ok and not self.active:
                self.active = True
                self.pressed.emit()
            # If modifiers NOT ok, we still suppressed the key. 
            # This is a trade-off: The trigger key is dedicated to PTT while this app is listening.
            
        elif event.event_type == 'up':
            if self.active:
                self.active = False
                self.released.emit()

