import settings

class StoryObject:
    def __init__(self, description, genre, heroes, mood):
        self.description = description
        self.genre = genre
        self.heroes = heroes if isinstance(heroes, list) else [h.strip() for h in heroes.split(';')]
        self.mood = mood

    def validate(self):
        if not self.description.strip():
            return "Описание истории не может быть пустым."
        if not self.genre.strip():
            return "Жанр не может быть пустым."
        if not self.heroes or not any(h.strip() for h in self.heroes):
            return "Укажите хотя бы одного персонажа."
        return None