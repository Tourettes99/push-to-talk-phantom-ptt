import sys
import platform

class AudioController:
    def __init__(self):
        self.os_type = platform.system().lower()
        self.backend = None
        
        if "windows" in self.os_type:
            self.backend = WindowsAudioBackend()
        elif "linux" in self.os_type:
            self.backend = LinuxAudioBackend()
        elif "darwin" in self.os_type: # macOS
            self.backend = MacAudioBackend()
        else:
            print(f"Unsupported OS: {self.os_type}")

    def get_input_devices(self):
        if self.backend:
            return self.backend.get_input_devices()
        return []

    def load_default_device(self):
        if self.backend:
            return self.backend.load_default_device()
        return False, "No Backend"

    def set_device(self, device_id):
        if self.backend:
            return self.backend.set_device(device_id)
        return False, "No Backend"
        
    def set_mute(self, is_muted):
        if self.backend:
            self.backend.set_mute(is_muted)

    def is_muted(self):
        if self.backend:
            return self.backend.is_muted()
        return False

# --- Windows Backend ---
class WindowsAudioBackend:
    def __init__(self):
        self.interface = None
        try:
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            from comtypes import CLSCTX_ALL
            self.AudioUtilities = AudioUtilities
            self.IAudioEndpointVolume = IAudioEndpointVolume
            self.CLSCTX_ALL = CLSCTX_ALL
        except ImportError:
            print("Pycaw/Comtypes not found.")

    def get_input_devices(self):
        results = []
        try:
            # Simple approach: List all visuals, try to guess if they are inputs?
            # Pycaw GetAllDevices returns everything. 
            # We will list all, and let the user pick.
            # Ideally we check for 'Capture' but standard Pycaw device objects don't make it easy without the Enum we failed on.
            # WORKAROUND: Use GetMicrophone() to get default, and listing allows generic selection.
            
            # Since listing caused crashes, let's strictly stick to safer methods.
            # If we simply return "Default Device" it works 100%. 
            # If the user WANTS selection, we try GetAllDevices but Wrap it carefully.
            
            devices = self.AudioUtilities.GetAllDevices()
            for d in devices:
                # We can't easily distinguish Input/Output without the Enum property store which crashed.
                # Use name heuristics? (Mic, Microphone, Input)
                name = d.FriendlyName
                lower_name = name.lower()
                
                # Keywords that suggest input
                input_keywords = ['mic', 'input', 'headset', 'transmit', 'webcam', 'line', 'phone', 'usb', 'hyperx', 'yeti', 'rode', 'virtual']
                # Keywords that suggest output ONLY (if not matched by input)
                output_keywords = ['speaker', 'monitor', 'tv', 'bravia', 'k380', 'nvidia']
                
                if any(x in lower_name for x in input_keywords):
                     # If it says "Speaker" but also "USB", it might be a combo device, but usually "Speakers (USB)" is output.
                     # Let's filter out "Speakers" if it doesn't also say "Mic" explicitly?
                     # Actually, many USB headsets appear as "Headset Earphone" (Output) and "Headset Microphone" (Input).
                     # We want to avoid listing the Output side if possible, but better to list too much than too little.
                     
                     results.append({'id': d.id, 'name': name})
            
            # Always add basic option
            results.insert(0, {'id': 'default', 'name': 'Default Communication Device'})
            
        except Exception as e:
            results.append({'id': 'error', 'name': f"WinListErr: {e}"})
        return results

    def load_default_device(self):
        return self.set_device('default')

    def set_device(self, device_id):
        import logging
        try:
            if device_id == 'default':
                # GetMicrophone() gets the default capture device
                device = self.AudioUtilities.GetMicrophone()
            else:
                # Find by ID
                devices = self.AudioUtilities.GetAllDevices()
                device = next((d for d in devices if d.id == device_id), None)
                
            if not device:
                return False, "Device not found"
            
            # Try to activate
            # ERROR HANDLING: user reported 'AudioDevice' has no Activate
            try:
                # OPTION 1: Explicit Activate (Standard Pycaw)
                self.interface = device.Activate(
                    self.IAudioEndpointVolume._iid_, self.CLSCTX_ALL, None)
            except AttributeError as ae:
                logging.error(f"Device Activate Error: {ae}. Properties: {dir(device)}")
                
                # OPTION 2: Use existing EndpointVolume if available (Pycaw wrapper often initializes it)
                if hasattr(device, 'EndpointVolume'):
                    logging.info("Using device.EndpointVolume directly")
                    # This is likely the IAudioEndpointVolume pointer already
                    self.interface = device.EndpointVolume
                
                # OPTION 3: Access underlying COM object _dev
                elif hasattr(device, '_dev'):
                     logging.info("Attempting activation on raw _dev")
                     self.interface = device._dev.Activate(
                        self.IAudioEndpointVolume._iid_, self.CLSCTX_ALL, None)
                else:
                    raise ae

            # Cast using comtypes native
            import comtypes
            try:
                self.volume = self.interface.QueryInterface(self.IAudioEndpointVolume)
            except Exception:
                # If it's already the interface (Option 2), query might fail or be redundant.
                # If self.interface is already the object, just use it.
                self.volume = self.interface
            
            return True, "Device Loaded"
        except Exception as e:
            logging.error(f"WinLoadErr Detail: {e}", exc_info=True)
            return False, f"WinLoadErr: {e}"

    def set_mute(self, is_muted):
        if self.volume:
            self.volume.SetMute(1 if is_muted else 0, None)
    
    def is_muted(self):
        if self.volume:
            return self.volume.GetMute() == 1
        return False

# --- Linux Backend ---
class LinuxAudioBackend:
    def __init__(self):
        self.pulse = None
        self.sink_source = None
        try:
            import pulsectl
            self.pulse = pulsectl.Pulse('phantom-ptt')
        except ImportError:
            print("pulsectl not installed. Install with `pip install pulsectl`")

    def get_input_devices(self):
        if not self.pulse: return []
        results = []
        for source in self.pulse.source_list():
            results.append({'id': source.index, 'name': source.description})
        return results

    def load_default_device(self):
        if not self.pulse: return False, "No PulseAudio"
        # Pick the server default?
        return True, "Default (Pulse)"

    def set_device(self, device_id):
        if not self.pulse: return False, "No PulseAudio"
        # We store the ID to mute later
        self.sink_source = device_id
        return True, f"Linux Device {device_id}"

    def set_mute(self, is_muted):
        if self.pulse and self.sink_source is not None:
             # Find source by ID and mute
             # This is a bit slow to do every keypress (searching list), but okay for Python
             # Optimization: Store source object?
             for s in self.pulse.source_list():
                 if s.index == self.sink_source or self.sink_source == 'default':
                      self.pulse.mute(s, is_muted)
                      break

    def is_muted(self):
        return False # TODO

# --- Mac Backend ---
class MacAudioBackend:
    def __init__(self):
        pass
        
    def get_input_devices(self):
        return [{'id': 'default', 'name': 'Default System Input'}]

    def load_default_device(self):
        return True, "Mac System Input"
        
    def set_device(self, device_id):
        return True, "Mac Input Selected"

    def set_mute(self, is_muted):
        import subprocess
        vol = 0 if is_muted else 100
        subprocess.run(f"osascript -e 'set volume input volume {vol}'", shell=True)
    
    def is_muted(self):
        return False
