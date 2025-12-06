#!/usr/bin/env python3
"""
Dnevnik.ru MCP Server

MCP сервер для работы с API Дневник.ру.
Предоставляет инструменты для получения расписания, оценок, домашних заданий.
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Any

import aiohttp
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from dnevnik_api import ExtendedDiaryAPI


# Загрузка конфигурации
def load_config() -> dict:
    """Загрузить конфигурацию из файла или переменных окружения."""
    config = {
        "token": os.getenv("DNEVNIK_TOKEN", ""),
        "person_id": int(os.getenv("DNEVNIK_PERSON_ID", "0")),
        "school_id": int(os.getenv("DNEVNIK_SCHOOL_ID", "0")),
        "group_id": int(os.getenv("DNEVNIK_GROUP_ID", "0")),
    }
    
    # Попробовать загрузить из config.json
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            file_config = json.load(f)
            config.update({k: v for k, v in file_config.items() if v})
    
    return config


CONFIG = load_config()
server = Server("dnevnik-mcp-server")


# ==========================================
# Вспомогательные функции
# ==========================================

def format_date(date: datetime) -> str:
    """Форматировать дату для API."""
    return date.strftime("%Y-%m-%d")


def today() -> str:
    return format_date(datetime.now())


def days_ago(n: int) -> str:
    return format_date(datetime.now() - timedelta(days=n))


def days_ahead(n: int) -> str:
    return format_date(datetime.now() + timedelta(days=n))


WEEKDAYS = {
    0: "Понедельник", 1: "Вторник", 2: "Среда",
    3: "Четверг", 4: "Пятница", 5: "Суббота", 6: "Воскресенье"
}


async def get_api() -> ExtendedDiaryAPI:
    """Создать экземпляр API."""
    session = aiohttp.ClientSession()
    return ExtendedDiaryAPI(session=session, token=CONFIG["token"])


def format_schedule(schedule_data: dict) -> str:
    """Форматировать расписание в читаемый вид."""
    result = []
    
    for day in schedule_data.get("days", []):
        date_str = day["date"][:10]
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        weekday = WEEKDAYS[date_obj.weekday()]
        
        lessons = day.get("lessons", [])
        if not lessons:
            result.append(f"\n{weekday}, {date_str} — выходной")
            continue
        
        result.append(f"\n{weekday}, {date_str}")
        result.append("-" * 30)
        
        subjects = {s["id"]: s["name"] for s in day.get("subjects", [])}
        sorted_lessons = sorted(lessons, key=lambda x: x.get("number", 0))
        
        for lesson in sorted_lessons:
            num = lesson.get("number", "?")
            hours = lesson.get("hours", "")
            subject_id = lesson.get("subjectId")
            subject_name = subjects.get(subject_id, "Неизвестный предмет")
            place = lesson.get("place", "")
            
            location = f" (каб. {place})" if place else ""
            result.append(f"  {num}. {hours} — {subject_name}{location}")
        
        # Домашние задания
        homeworks = day.get("homeworks", [])
        if homeworks:
            result.append("\n  📝 Домашние задания:")
            for hw in homeworks:
                subject_id = hw.get("subjectId")
                subject_name = subjects.get(subject_id, "?")
                text = hw.get("text", "Без описания")
                result.append(f"    • {subject_name}: {text}")
    
    return "\n".join(result) if result else "Расписание не найдено"


def format_marks(marks_data: list) -> str:
    """Форматировать оценки в читаемый вид."""
    if not marks_data:
        return "Оценок за указанный период нет"
    
    # Группируем по предметам
    by_subject = {}
    for mark in marks_data:
        subject = mark.get("subject", {}).get("name", "Неизвестный предмет")
        value = mark.get("value", "?")
        date = mark.get("date", "")[:10]
        
        if subject not in by_subject:
            by_subject[subject] = []
        by_subject[subject].append(f"{value} ({date})")
    
    result = ["📊 Оценки:\n"]
    for subject, marks in sorted(by_subject.items()):
        result.append(f"  {subject}: {', '.join(marks)}")
    
    return "\n".join(result)


def format_homework(homework_data: list) -> str:
    """Форматировать домашние задания."""
    if not homework_data:
        return "Домашних заданий нет"
    
    result = ["📝 Домашние задания:\n"]
    for hw in homework_data:
        subject = hw.get("subject", {}).get("name", "?")
        text = hw.get("text", "Без описания")
        date = hw.get("date", "")[:10]
        result.append(f"  [{date}] {subject}: {text}")
    
    return "\n".join(result)


# ==========================================
# Определение инструментов MCP
# ==========================================

@server.list_tools()
async def list_tools() -> list[Tool]:
    """Список доступных инструментов."""
    return [
        # Информация
        Tool(
            name="get_user_info",
            description="Получить информацию о текущем пользователе (имя, роль, школа)",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="get_context",
            description="Получить контекст пользователя (школы, классы, роли)",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        
        # Расписание
        Tool(
            name="get_schedule",
            description="Получить расписание ученика за указанный период",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "Начальная дата (YYYY-MM-DD)"},
                    "end_date": {"type": "string", "description": "Конечная дата (YYYY-MM-DD)"}
                },
                "required": ["start_date", "end_date"]
            }
        ),
        Tool(
            name="get_schedule_today",
            description="Получить расписание на сегодня",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="get_schedule_week",
            description="Получить расписание на текущую неделю",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        
        # Оценки
        Tool(
            name="get_marks",
            description="Получить оценки за указанный период",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "Начальная дата (YYYY-MM-DD)"},
                    "end_date": {"type": "string", "description": "Конечная дата (YYYY-MM-DD)"}
                },
                "required": ["start_date", "end_date"]
            }
        ),
        Tool(
            name="get_marks_recent",
            description="Получить оценки за последние 7 дней",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="get_final_marks",
            description="Получить итоговые оценки за текущий период",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="get_average_marks",
            description="Получить средние оценки по предметам",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        
        # Домашние задания
        Tool(
            name="get_homework",
            description="Получить домашние задания за период",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "Начальная дата"},
                    "end_date": {"type": "string", "description": "Конечная дата"}
                },
                "required": ["start_date", "end_date"]
            }
        ),
        Tool(
            name="get_homework_week",
            description="Получить домашние задания на текущую неделю",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        
        # Класс и школа
        Tool(
            name="get_classmates",
            description="Получить список одноклассников",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="get_teachers",
            description="Получить список учителей класса",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="get_subjects",
            description="Получить список предметов класса",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="get_school_groups",
            description="Получить все классы школы (требуются права администратора)",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        
        # Посещаемость
        Tool(
            name="get_attendance",
            description="Получить посещаемость за период",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "Начальная дата"},
                    "end_date": {"type": "string", "description": "Конечная дата"}
                },
                "required": ["start_date", "end_date"]
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Обработка вызова инструмента."""
    
    api = await get_api()
    
    try:
        if name == "get_user_info":
            data = await api.get_info()
            result = f"👤 Пользователь: {data.get('lastName', '')} {data.get('firstName', '')}\n"
            result += f"ID: {data.get('id')}\n"
            result += f"Роль: {data.get('type', 'неизвестно')}"
            
        elif name == "get_context":
            data = await api.get_context()
            result = json.dumps(data, ensure_ascii=False, indent=2)
            
        elif name == "get_schedule":
            data = await api.get_person_schedule(
                str(CONFIG["person_id"]),
                str(CONFIG["group_id"]),
                arguments["start_date"],
                arguments["end_date"]
            )
            result = format_schedule(data)
            
        elif name == "get_schedule_today":
            data = await api.get_person_schedule(
                str(CONFIG["person_id"]),
                str(CONFIG["group_id"]),
                today(),
                today()
            )
            result = format_schedule(data)
            
        elif name == "get_schedule_week":
            data = await api.get_person_schedule(
                str(CONFIG["person_id"]),
                str(CONFIG["group_id"]),
                today(),
                days_ahead(7)
            )
            result = format_schedule(data)
            
        elif name == "get_marks":
            data = await api.get_person_marks(
                CONFIG["person_id"],
                CONFIG["school_id"],
                arguments["start_date"],
                arguments["end_date"]
            )
            result = format_marks(data)
            
        elif name == "get_marks_recent":
            data = await api.get_person_marks(
                CONFIG["person_id"],
                CONFIG["school_id"],
                days_ago(7),
                today()
            )
            result = format_marks(data)
            
        elif name == "get_final_marks":
            data = await api.get_person_group_marks_final(
                CONFIG["person_id"],
                CONFIG["group_id"]
            )
            result = json.dumps(data, ensure_ascii=False, indent=2)
            
        elif name == "get_average_marks":
            data = await api.get_group_average_marks(
                CONFIG["group_id"],
                days_ago(30),
                today()
            )
            result = json.dumps(data, ensure_ascii=False, indent=2)
            
        elif name == "get_homework":
            data = await api.get_school_homework(
                CONFIG["school_id"],
                arguments["start_date"],
                arguments["end_date"]
            )
            result = format_homework(data)
            
        elif name == "get_homework_week":
            data = await api.get_school_homework(
                CONFIG["school_id"],
                today(),
                days_ahead(7)
            )
            result = format_homework(data)
            
        elif name == "get_classmates":
            data = await api.get_classmates()
            result = "👥 Одноклассники:\n"
            for person in data:
                result += f"  • {person.get('lastName', '')} {person.get('firstName', '')}\n"
                
        elif name == "get_teachers":
            data = await api.get_group_teachers(CONFIG["group_id"])
            result = "👨‍🏫 Учителя класса:\n"
            for teacher in data:
                result += f"  • {teacher.get('lastName', '')} {teacher.get('firstName', '')}\n"
                
        elif name == "get_subjects":
            data = await api.get_group_subjects(CONFIG["group_id"])
            result = "📚 Предметы:\n"
            for subject in data:
                result += f"  • {subject.get('name', 'Неизвестно')}\n"
                
        elif name == "get_school_groups":
            data = await api.get_school_groups(CONFIG["school_id"])
            result = "🏫 Классы школы:\n"
            for group in data:
                result += f"  • {group.get('name', '?')} (ID: {group.get('id')})\n"
                
        elif name == "get_attendance":
            data = await api.get_person_attendance(
                CONFIG["person_id"],
                arguments["start_date"],
                arguments["end_date"]
            )
            result = json.dumps(data, ensure_ascii=False, indent=2)
            
        else:
            result = f"Неизвестный инструмент: {name}"
            
    except Exception as e:
        result = f"Ошибка: {str(e)}"
    finally:
        await api._session.close()
    
    return [TextContent(type="text", text=result)]


# ==========================================
# Запуск сервера
# ==========================================

async def main():
    """Запуск MCP сервера."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
