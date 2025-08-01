import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from gui import MainWindow
import qasync
import asyncio

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    font = QFont("Segoe UI")
    app.setFont(font)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    window = MainWindow()
    window.show()

    with loop:
        loop.run_forever()