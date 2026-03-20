# Tech Context

## Стек технологий
- **Язык**: Python 3.13
- **Telegram Bot**: aiogram 2.x
- **База данных**: SQLite (через SQLAlchemy)
- **Планировщик**: APScheduler
- **Деплой**: Render (Web Service)

## Окружение
- Python 3.13
- pip/requirements.txt

## Зависимости (requirements.txt)
- aiogram
- APScheduler
- python-dotenv

## Ограничения
- Бесплатный инстанс на Render (может засыпать)
- SQLite (не для высоких нагрузок)

## CI/CD
- GitHub → Render (автоматический деплой)