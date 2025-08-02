import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from gui import MainWindow
from story_generator import StoryGeneratorWorker
from StoryObject import StoryObject 

class StoryAppLogic:
    def __init__(self, gui_window):
        self.gui = gui_window
        self.worker = None
        self.gui.storyRequested.connect(self.generate_story)

    def generate_story(self, story_object: StoryObject):
        self.worker = StoryGeneratorWorker(story_object)
        self.worker.finished.connect(self.on_story_generated)
        self.worker.error.connect(self.on_generation_error)
        self.worker.start()

    def on_story_generated(self, result):
        self.gui.set_story_data(result) 
        self.gui.enable_generation_button(True)

    def on_generation_error(self, error_msg):
        self.gui.show_error(error_msg)
        self.gui.set_generation_status("Произошла ошибка при генерации. Попробуйте еще раз.")
        self.gui.enable_generation_button(True)

    def cleanup(self):
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    font = QFont("Segoe UI")
    app.setFont(font)
    window = MainWindow()
    logic = StoryAppLogic(window)

    window.show()
    try:
        exit_code = app.exec_()
        logic.cleanup()
        sys.exit(exit_code)
    except SystemExit:
        logic.cleanup()
        pass

if __name__ == "__main__":
    main()
