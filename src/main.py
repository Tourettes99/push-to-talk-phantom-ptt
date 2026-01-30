import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
import installer

def main():
    # Attempt install if running as frozen exe
    installer.install()

    app = QApplication(sys.argv)
    
    # Apply global styling here or in the window
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
