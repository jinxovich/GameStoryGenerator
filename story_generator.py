import asyncio
from PyQt5.QtCore import QThread, pyqtSignal
import ai
from StoryObject import StoryObject

class StoryGeneratorWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, story_object: StoryObject):
        super().__init__()
        self.story_object = story_object

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            story_data = loop.run_until_complete(ai.get_story_from_ai(self.story_object))
            
            if story_data:
                self.finished.emit(story_data)
            else:
                self.error.emit("AI не вернул результат. Попробуйте изменить запрос.")
                
        except Exception as e:
            self.error.emit(f"Ошибка: {str(e)}")
        finally:
            loop.close()