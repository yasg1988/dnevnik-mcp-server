# Dnevnik.ru MCP Server

MCP (Model Context Protocol) сервер для работы с API Дневник.ру.
Позволяет ИИ-ассистентам (Claude, etc.) получать расписание, оценки, домашние задания.

## Возможности

- 📅 Расписание уроков на любой период
- 📊 Оценки ученика (текущие и итоговые)
- 📝 Домашние задания
- 👥 Информация о классе, учителях, одноклассниках
- 🏫 Данные о школе (для администраторов)
- ✅ Посещаемость уроков

## Установка

```bash
# Клонировать репозиторий
git clone https://github.com/yasg1988/dnevnik-mcp-server.git
cd dnevnik-mcp-server

# Установить зависимости
pip install -r requirements.txt

# Создать конфигурацию
cp config.example.json config.json
# Отредактировать config.json - добавить токен
```

## Получение токена

1. Авторизоваться на https://login.dnevnik.ru/login
2. Перейти по ссылке:
   ```
   https://login.dnevnik.ru/oauth2?response_type=token&client_id=b8006d75-70a9-4291-885c-13d8511bb2ae&scope=CommonInfo,EducationalInfo
   ```
3. Нажать "Разрешить"
4. Скопировать токен из URL после `access_token=`

## Настройка Claude Desktop

Добавить в `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "dnevnik": {
      "command": "python",
      "args": ["C:/path/to/dnevnik-mcp-server/server.py"],
      "env": {
        "DNEVNIK_TOKEN": "ваш_токен",
        "DNEVNIK_PERSON_ID": "1234567890",
        "DNEVNIK_SCHOOL_ID": "1234567890",
        "DNEVNIK_GROUP_ID": "1234567890"
      }
    }
  }
}
```

Или использовать config.json (сервер автоматически его прочитает).

## Доступные инструменты (Tools)

### Информация о пользователе
| Tool | Описание |
|------|----------|
| `get_user_info` | Информация о текущем пользователе |
| `get_context` | Контекст пользователя (школы, классы) |

### Расписание
| Tool | Описание |
|------|----------|
| `get_schedule` | Расписание ученика на период |
| `get_schedule_today` | Расписание на сегодня |
| `get_schedule_week` | Расписание на неделю |

### Оценки
| Tool | Описание |
|------|----------|
| `get_marks` | Оценки за период |
| `get_marks_recent` | Последние оценки (7 дней) |
| `get_final_marks` | Итоговые оценки |
| `get_average_marks` | Средние оценки по предметам |

### Домашние задания
| Tool | Описание |
|------|----------|
| `get_homework` | Домашние задания на период |
| `get_homework_week` | ДЗ на текущую неделю |

### Класс и школа
| Tool | Описание |
|------|----------|
| `get_classmates` | Одноклассники |
| `get_teachers` | Учителя класса |
| `get_subjects` | Предметы класса |
| `get_school_groups` | Все классы школы (для админов) |

### Посещаемость
| Tool | Описание |
|------|----------|
| `get_attendance` | Посещаемость за период |
| `set_attendance` | Отметить посещаемость (для учителей) |

## Примеры использования в Claude

```
Пользователь: Покажи расписание на завтра

Claude: [использует get_schedule_today]
Вот расписание на завтра:
1. 08:30 — Математика (каб. 205)
2. 09:20 — Русский язык (каб. 301)
...
```

```
Пользователь: Какие оценки получил за последнюю неделю?

Claude: [использует get_marks_recent]
За последнюю неделю получены оценки:
- Математика: 5, 4
- Русский язык: 5
...
```

## Лицензия

MIT

## Связанные проекты

- [pydnevnikruapi](https://github.com/kesha1225/DnevnikRuAPI) - Python библиотека
- [pydnevnikruapi-extended](https://github.com/yasg1988/pydnevnikruapi-extended) - расширенная версия
