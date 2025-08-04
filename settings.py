# Настройки для генерации истории в виде словарей
# Каждый словарь содержит:
# - 'options': список доступных вариантов (каждый с 'name' для UI и 'value' для AI)
# - 'default': значение по умолчанию, которое будет использоваться при запуске

MOODS = {
    'default': 'neutral',
    'options': [
        {'name': 'Нейтральное', 'value': 'neutral'},
        {'name': 'Напряженное', 'value': 'tense'},
        {'name': 'Мрачное и готическое', 'value': 'dark_and_gothic'},
        {'name': 'Светлое и оптимистичное', 'value': 'light_and_optimistic'},
        {'name': 'Трагическое', 'value': 'tragic'},
        {'name': 'Комическое и абсурдное', 'value': 'comedic_and_absurd'},
        {'name': 'Меланхоличное', 'value': 'melancholic'},
    ]
}