# Phantom PTT

Phantom PTT is a global Push-to-Talk (PTT) utility that allows you to mute your microphone system-wide or for specific devices. It features "Input Suppression" which prevents your PTT key (e.g., 'Num 0' or '5') from typing in other applications while the PTT is active.

## Features
- **Global Hotkey Support**: Works even when the app is in the background.
- **Input Suppression**: The trigger key is blocked from reaching the active window (no more spamming 'v' in chat).
- **Device Selection**: Choose specific input devices or use the default communication device.
- **Persistent Settings**: Remembers your hotkey and device choice.

---

## getting Started

### 🖥️ Windows
**Using the Executable (Recommended)**
1.  Simply run `PhantomPTT.exe` included in this folder.
2.  Select your Input Device from the dropdown.
3.  Type your desired hotkey (e.g., `num 0`, `v`, `ctrl+alt+p`) and click **ACTIVATE / UPDATE**.
4.  Status will turn **Available**. Hold the key to talk!

**Data Location**: Configuration is saved to `~/.phantom_ptt_config.json`.

---

### 🐧 Linux
**Running from this folder:**

1.  Open a terminal in this folder.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: You may need to run `pip` or the script as `sudo` for global key interception privileges.*

3.  Run the app:
    ```bash
    sudo python src/main.py
    ```

---

### 🍎 macOS
**Running from this folder:**

1.  Open a terminal in this folder.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  Run the app:
    ```bash
    sudo python src/main.py
    ```
**Permissions**: You must grant the terminal application "Input Monitoring" and "Accessibility" permissions in `System Settings > Privacy & Security` for the global hotkey to work.
*Note: Depending on MacOS version, strict security might interfere with global key interception. Ensure permissions are granted.*

---

## Troubleshooting
- **Device Not Saving?** Check `~/.phantom_ptt_debug.log` for details.
- **Key Not Working?** Ensure no other app with high-level hooks (like some anti-cheat) is blocking it. Try running as Administrator/Root.
