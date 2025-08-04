# Настройки для генерации истории в виде словарей
# Каждый словарь содержит:
# - 'options': список доступных вариантов (каждый с 'name' для UI и 'value' для AI)
# - 'default': значение по умолчанию, которое будет использоваться при запуске

NARRATIVE_STYLES = {
    'default': 'classic',
    'options': [
        {'name': 'Классический линейный', 'value': 'classic'},
        {'name': 'Параллельные сюжеты', 'value': 'parallel'},
        {'name': 'С флешбеками', 'value': 'flashback'},
        {'name': 'Эпистолярный (в письмах)', 'value': 'epistolary'},
        {'name': 'Поток сознания', 'value': 'stream_of_consciousness'},
    ]
}

MOODS = {
    'default': 'tense',
    'options': [
        {'name': 'Напряженное', 'value': 'tense'},
        {'name': 'Мрачное и готическое', 'value': 'dark_and_gothic'},
        {'name': 'Светлое и оптимистичное', 'value': 'light_and_optimistic'},
        {'name': 'Трагическое', 'value': 'tragic'},
        {'name': 'Комическое и абсурдное', 'value': 'comedic_and_absurd'},
        {'name': 'Меланхоличное', 'value': 'melancholic'},
    ]
}

THEMES = {
    'default': 'survival',
    'options': [
        {'name': 'Выживание', 'value': 'survival'},
        {'name': 'Любовь и потеря', 'value': 'love_and_loss'},
        {'name': 'Предательство и месть', 'value': 'betrayal_and_revenge'},
        {'name': 'Поиск справедливости', 'value': 'quest_for_justice'},
        {'name': 'Борьба за свободу', 'value': 'fight_for_freedom'},
        {'name': 'Власть и коррупция', 'value': 'power_and_corruption'},
    ]
}

CONFLICTS = {
    'default': 'man_vs_man',
    'options': [
        {'name': 'Человек против человека', 'value': 'man_vs_man'},
        {'name': 'Человек против себя', 'value': 'man_vs_self'},
        {'name': 'Человек против природы', 'value': 'man_vs_nature'},
        {'name': 'Человек против общества', 'value': 'man_vs_society'},
        {'name': 'Человек против технологии', 'value': 'man_vs_technology'},
    ]
}