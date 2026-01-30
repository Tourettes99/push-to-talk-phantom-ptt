import json
import os
import platform

# Determine robust path
if platform.system() == "Windows":
    base_dir = os.environ.get("USERPROFILE") or os.path.expanduser("~")
else:
    base_dir = os.path.expanduser("~")

CONFIG_FILE = os.path.join(base_dir, ".phantom_ptt_config.json")

DEFAULT_CONFIG = {
    "hotkey": "num 0",
    "device_id": None
}

def load_config():
    """Box loads the configuration from file, or returns default if not found."""
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_CONFIG.copy()
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            data = json.load(f)
            # Merge with default to ensure all keys exist
            config = DEFAULT_CONFIG.copy()
            config.update(data)
            return config
    except Exception as e:
        return DEFAULT_CONFIG.copy()

def save_config(config):
    """Saves the configuration to file."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Error saving config: {e}")
