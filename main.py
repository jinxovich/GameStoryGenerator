import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from gui import MainWindow


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    font = QFont("Segoe UI")
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())