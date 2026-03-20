# System Patterns

## Архитектура
```
school_help_bot/
├── main.py              # Главный файл бота, точка входа
├── database/            # Работа с БД
│   ├── models.py        # SQLAlchemy модели
│   └── setup.py         # Инициализация БД
├── handlers/            # Обработчики команд
│   ├── common.py        # /start, /help, /schedule
│   ├── schedule.py      # Управление расписанием
│   └── admin.py         # Управление классами
└── services/            # Дополнительные сервисы
    └── scheduler.py     # Планировщик напоминаний
```

## Связи подсистем
- main.py инициализирует бота и регистрирует обработчики
- handlers используют database для работы с данными
- services/scheduler использует database для проверки заданий

## Паттерны
- MVC-подобная структура (handlers = controllers, database = models)
- Интеграция с Telegram Bot API через aiogram