import asyncio
from PyQt5.QtCore import QThread, pyqtSignal
import ai
from StoryObject import StoryObject

class StoryGeneratorWorker(QThread):
    """Выполняет асинхронный запрос к AI в отдельном потоке."""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, story_object: StoryObject):
        super().__init__()
        self.story_object = story_object

    def run(self):
        try:
            # Создаем и управляем циклом событий asyncio внутри потока
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Запускаем асинхронную задачу и ждем ее выполнения
            story_data = loop.run_until_complete(ai.get_story_from_ai(self.story_object))
            
            if story_data:
                self.finished.emit(story_data)
            else:
                self.error.emit("AI не вернул результат. Попробуйте изменить запрос.")
                
        except Exception as e:
            # Перехватываем любые исключения и отправляем сигнал ошибки
            self.error.emit(f"Ошибка: {str(e)}")
        finally:
            # Гарантированно закрываем цикл событий
            loop.close()