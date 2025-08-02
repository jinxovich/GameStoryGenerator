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
        self.heroes = heroes
        self.narrative_style = narrative_style
        self.mood = mood
        self.theme = theme
        self.conflict = conflict


def create_story_object(self):
    desc = self.desc_input.edit.toPlainText().strip()
    heroes_text = self.heroes_input.edit.toPlainText().strip()
    heroes = [h.strip() for h in heroes_text.split(',') if h.strip()]
    genre = self.genre_input.edit.toPlainText().strip()
    narrative_style = self.narrative_style_combo.combo.currentText()
    mood = self.mood_combo.combo.currentText()
    theme = self.theme_combo.combo.currentText()
    conflict = self.conflict_combo.combo.currentText()
    is_adult = self.adult_checkbox.isChecked()

    return StoryObject(
        description=desc,
        genre=genre,
        heroes=heroes,
        narrative_style=narrative_style,
        mood=mood,
        theme=theme,
        conflict=conflict,
        adult=is_adult
    )