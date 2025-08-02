import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QThread
from gui import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    font = QFont("Segoe UI")
    app.setFont(font)
    
    window = MainWindow()
    window.show()

    try:
        sys.exit(app.exec_())
    except SystemExit:
        pass

if __name__ == "__main__":
    main()