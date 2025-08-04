import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont

from gui import MainWindow
from story_generator import StoryGeneratorWorker
from StoryObject import StoryObject

class ApplicationLogic:
    """Связывает GUI с логикой генерации истории."""
    def __init__(self, main_window: MainWindow):
        self.gui = main_window
        self.worker = None
        self.gui.storyRequested.connect(self.start_story_generation)

    def start_story_generation(self, story_object: StoryObject):
        """Запускает воркер для генерации истории в отдельном потоке."""
        self.worker = StoryGeneratorWorker(story_object)
        self.worker.finished.connect(self.gui.set_story_data)
        self.worker.error.connect(self.gui.handle_generation_error)
        self.worker.start()

    def cleanup_on_exit(self):
        """Корректно завершает работу воркера при выходе."""
        if self.worker and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait()

def main():
    """Основная функция запуска приложения."""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Установка глобального шрифта
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Создание и запуск
    window = MainWindow()
    logic = ApplicationLogic(window)
    window.show()
    
    # Обеспечение корректного выхода
    exit_code = app.exec_()
    logic.cleanup_on_exit()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()