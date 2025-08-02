from settings import (
    DEFAULT_NARRATIVE_STYLE, DEFAULT_MOOD, 
    DEFAULT_THEME, DEFAULT_CONFLICT
)

class StoryObject:
    def __init__(self, description, genre, heroes, 
                narrative_style=DEFAULT_NARRATIVE_STYLE, 
                mood=DEFAULT_MOOD, 
                theme=DEFAULT_THEME, 
                conflict=DEFAULT_CONFLICT):
        self.description = description
        self.genre = genre
        self.heroes = heroes if isinstance(heroes, list) else [heroes]
        self.narrative_style = narrative_style
        self.mood = mood
        self.theme = theme
        self.conflict = conflict
        
    def to_dict(self):
        return {
            'description': self.description,
            'genre': self.genre,
            'heroes': self.heroes,
            'narrative_style': self.narrative_style,
            'mood': self.mood,
            'theme': self.theme,
            'conflict': self.conflict,
            'adult': self.adult
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            description=data.get('description', ''),
            genre=data.get('genre', ''),
            heroes=data.get('heroes', []),
            narrative_style=data.get('narrative_style', DEFAULT_NARRATIVE_STYLE),
            mood=data.get('mood', DEFAULT_MOOD),
            theme=data.get('theme', DEFAULT_THEME),
            conflict=data.get('conflict', DEFAULT_CONFLICT),
        )
    
    def validate(self):
        errors = []
        
        if not self.description or not self.description.strip():
            errors.append("Описание истории не может быть пустым")
            
        if not self.genre or not self.genre.strip():
            errors.append("Жанр не может быть пустым")
            
        if not self.heroes or (len(self.heroes) == 1 and not self.heroes[0].strip()):
            errors.append("Должен быть указан хотя бы один персонаж")
            
        if len(self.description) > 1000:
            errors.append("Описание истории слишком длинное (максимум 1000 символов)")
            
        valid_heroes = [h for h in self.heroes if h.strip()]
        if len(valid_heroes) > 10:
            errors.append("Слишком много персонажей (максимум 10)")
            
        return errors
    
    def get_summary(self):
        heroes_str = ', '.join([h for h in self.heroes if h.strip()])
        
        summary = f"""Жанр: {self.genre}
Персонажи: {heroes_str}
Стиль: {self.narrative_style}
Настроение: {self.mood}
Тема: {self.theme}
Конфликт: {self.conflict}

Описание:
{self.description[:200]}{'...' if len(self.description) > 200 else ''}"""
        
        return summary


def create_story_object(self):
    desc = self.desc_input.edit.toPlainText().strip()
    heroes_text = self.heroes_input.edit.toPlainText().strip()
    heroes = [h.strip() for h in heroes_text.split(',') if h.strip()]
    genre = self.genre_input.edit.toPlainText().strip()
    narrative_style = self.narrative_style_combo.combo.currentText()
    mood = self.mood_combo.combo.currentText()
    theme = self.theme_combo.combo.currentText()
    conflict = self.conflict_combo.combo.currentText()

    return StoryObject(
        description=desc,
        genre=genre,
        heroes=heroes,
        narrative_style=narrative_style,
        mood=mood,
        theme=theme,
        conflict=conflict,
    )