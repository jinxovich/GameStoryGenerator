from settings import (
    DEFAULT_NARRATIVE_STYLE, DEFAULT_MOOD, 
    DEFAULT_THEME, DEFAULT_CONFLICT, DEFAULT_ADULT
)

class StoryObject:
    def __init__(self, description, genre, heroes, 
                 narrative_style=DEFAULT_NARRATIVE_STYLE, 
                 mood=DEFAULT_MOOD, 
                 theme=DEFAULT_THEME, 
                 conflict=DEFAULT_CONFLICT, 
                 adult=DEFAULT_ADULT):
        self.description = description
        self.genre = genre
        self.heroes = heroes
        self.narrative_style = narrative_style
        self.mood = mood
        self.theme = theme
        self.conflict = conflict
        self.adult = adult