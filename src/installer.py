import os
import sys
import shutil
import subprocess

APP_NAME = "PhantomPTT"
INSTALL_DIR = os.path.join(os.getenv('APPDATA'), APP_NAME)
EXE_NAME = "PhantomPTT.exe"

def is_installed():
    # Check if we are running from the install dir
    # This logic assumes we are frozen (PyInstaller). 
    # If standard python, we skip internal install logic usually or just copy source.
    
    if getattr(sys, 'frozen', False):
        current_exe = sys.executable
        return current_exe.startswith(INSTALL_DIR)
    else:
        # Dev mode usually
        return True

def install(force=False):
    """
    Copies the executable to AppData and creates a shortcut.
    """
    if not getattr(sys, 'frozen', False) and not force:
        print("Not running as frozen exe, skipping self-install.")
        return

    if not os.path.exists(INSTALL_DIR):
        os.makedirs(INSTALL_DIR)

    current_exe = sys.executable
    target_exe = os.path.join(INSTALL_DIR, EXE_NAME)

    try:
        if current_exe != target_exe:
            shutil.copy2(current_exe, target_exe)
            print(f"Installed to {target_exe}")
            
        create_shortcut(target_exe)
        
        # Optional: Ask to restart from new location?
        # subprocess.Popen([target_exe])
        # sys.exit(0)
        
    except Exception as e:
        print(f"Installation failed: {e}")

def create_shortcut(target_path):
    desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop') 
    shortcut_path = os.path.join(desktop, f"{APP_NAME}.lnk")
    
    # Create VBS script to generate shortcut
    vbs_path = os.path.join(INSTALL_DIR, "create_shortcut.vbs")
    vbs_content = f"""
    Set oWS = WScript.CreateObject("WScript.Shell")
    sLinkFile = "{shortcut_path}"
    Set oLink = oWS.CreateShortcut(sLinkFile)
    oLink.TargetPath = "{target_path}"
    oLink.WorkingDirectory = "{os.path.dirname(target_path)}"
    oLink.Description = "Phantom PTT Launcher"
    oLink.Save
    """
    
    with open(vbs_path, "w") as f:
        f.write(vbs_content)
        
    subprocess.run(["cscript", "//Nologo", vbs_path], shell=True)
    os.remove(vbs_path)
    print(f"Shortcut created at {shortcut_path}")

