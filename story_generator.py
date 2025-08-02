import asyncio
import json
from PyQt5.QtCore import QThread, pyqtSignal
import ai 

class StoryGenerationError(Exception):
    pass

class StoryGeneratorWorker(QThread):

    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, story_object):
        super().__init__()
        self.story_object = story_object

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(ai.get(self.story_object))
                if result:
                    self.finished.emit(result)
                else:
                    self.error.emit("Не удалось получить ответ от AI")
            finally:
                loop.close()
        except Exception as e:
            self.error.emit(f"Ошибка при генерации: {str(e)}")
