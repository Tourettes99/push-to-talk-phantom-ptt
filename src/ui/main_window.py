from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QLabel, QLineEdit, QPushButton, QMessageBox, QComboBox) # Added QComboBox
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QIcon
from ui.visuals import VisualsWidget
from audio_manager import AudioController
from key_listener import PTTListener
import os
import logging
import config

# Setup logging
log_path = os.path.expanduser("~/.phantom_ptt_debug.log")
logging.basicConfig(filename=log_path, level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Phantom PTT")
        self.resize(600, 450) # Taller for combo box
        
        logging.info("App Started")
        
        # Core Logic
        self.audio = AudioController()
        self.listener = PTTListener()
        self.listener.pressed.connect(self.on_ptt_press)
        self.listener.released.connect(self.on_ptt_release)
        
        self.devices = []
        
        # Load Config
        self.app_config = config.load_config()
        logging.info(f"Loaded Config: {self.app_config}")
        self.current_hotkey = self.app_config.get("hotkey", "num 0")
        
        # Setup UI
        self.stack_ui()
        
        # Initialize
        self.refresh_devices()
        self.hotkey_input.setText(self.current_hotkey)
        self.apply_hotkey()

    def stack_ui(self):
        self.visuals = VisualsWidget()
        self.setCentralWidget(self.visuals)
        
        layout = QVBoxLayout(self.visuals)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        title = QLabel("PHANTOM PTT")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: white; margin-bottom: 20px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Controls Container
        controls = QWidget()
        controls.setStyleSheet("background: rgba(0, 0, 0, 150); border: 1px solid white; border-radius: 5px;")
        c_layout = QVBoxLayout(controls)
        
        # Device Selector
        lbl_dev = QLabel("INPUT DEVICE:")
        lbl_dev.setStyleSheet("color: white; font-family: monospace; font-size: 10px;")
        self.combo_dev = QComboBox()
        self.combo_dev.setStyleSheet("""
            QComboBox { background: rgba(0,0,0,100); color: white; border: 1px solid gray; }
            QComboBox QAbstractItemView { background: black; color: white; selection-background-color: blue; }
        """)
        # Connect to USER action handler
        self.combo_dev.currentIndexChanged.connect(self.on_user_device_change)
        
        c_layout.addWidget(lbl_dev)
        c_layout.addWidget(self.combo_dev)
        
        # Hotkey Input
        lbl_key = QLabel("TRIGGER KEY :")
        lbl_key.setStyleSheet("color: white; font-family: monospace;")
        self.hotkey_input = QLineEdit()
        self.hotkey_input.setPlaceholderText("e.g. 'ctrl+v' or 'num 0'")
        self.hotkey_input.setStyleSheet("color: white; background: transparent; border-bottom: 1px solid white;")
        
        btn_apply = QPushButton("ACTIVATE / UPDATE")
        btn_apply.setStyleSheet("background: white; color: black; font-weight: bold; padding: 5px;")
        btn_apply.clicked.connect(self.apply_hotkey)
        
        c_layout.addWidget(lbl_key)
        c_layout.addWidget(self.hotkey_input)
        c_layout.addWidget(btn_apply)
        
        layout.addWidget(controls)
        
        # Status
        self.status_label = QLabel("STATUS: IDLE")
        self.status_label.setStyleSheet("color: lime; font-family: monospace; font-size: 14px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Device Info (Keep for debug, or use as active status)
        self.device_label = QLabel("Initializing...")
        self.device_label.setStyleSheet("color: gray; font-size: 10px;")
        self.device_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.device_label)
        
    def refresh_devices(self):
        logging.info("Refreshing devices...")
        self.devices = self.audio.get_input_devices()
        
        self.combo_dev.blockSignals(True) # Prevent triggering on_user_device_change
        self.combo_dev.clear()
        
        saved_id = self.app_config.get("device_id")
        target_index = 0
        
        for i, dev in enumerate(self.devices):
            self.combo_dev.addItem(dev['name'], dev['id'])
            # Log for debug
            # logging.info(f"Examining Dev: {dev['name']} ID: {dev['id']} vs Saved: {saved_id}")
            if saved_id is not None and str(dev['id']) == str(saved_id):
                target_index = i
                logging.info(f"Found match at index {i}")
            
        self.combo_dev.setCurrentIndex(target_index)
        self.combo_dev.blockSignals(False)
        
        # Apply without saving (load phase)
        self._activate_device(save=False)

    def on_user_device_change(self, index):
        # Triggered by user interaction
        self._activate_device(save=True)

    def _activate_device(self, save=False):
        if self.combo_dev.currentIndex() < 0: return
        
        dev_id = self.combo_dev.currentData()
        name = self.combo_dev.currentText()
        logging.info(f"Activating device: {name} [{dev_id}] Save={save}")
        
        success, msg = self.audio.set_device(dev_id)
        if success:
             self.device_label.setText(f"Active: {name[:30]}")
             if save:
                 self.app_config["device_id"] = dev_id
                 config.save_config(self.app_config)
                 logging.info("Config saved.")
        else:
             self.device_label.setText(f"Error: {msg}")
             logging.error(f"Failed to set device: {msg}")

    def apply_hotkey(self):
        key = self.hotkey_input.text()
        if not key:
            return
            
        self.current_hotkey = key
        # Save to config
        self.app_config["hotkey"] = self.current_hotkey
        config.save_config(self.app_config)
        
        self.device_label.setText(f"Target: {self.combo_dev.currentText()}")
        
        # Init Listener
        try:
            self.listener.start_listening(self.current_hotkey)
            self.status_label.setText("SYSTEM ARMED - READY")
            self.status_label.setStyleSheet("color: #00ffff;")
        except Exception as e:
            self.status_label.setText(f"KEY ERROR: {e}")

    @pyqtSlot()
    def on_ptt_press(self):
        self.status_label.setText("<<< TRANSMITTING >>>")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        self.audio.set_mute(False) # Unmute

    @pyqtSlot()
    def on_ptt_release(self):
        self.status_label.setText("--- MUTED ---")
        self.status_label.setStyleSheet("color: gray;")
        self.audio.set_mute(True) # Mute
