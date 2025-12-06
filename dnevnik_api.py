"""
Расширенная обёртка для pydnevnikruapi
Копия из https://github.com/yasg1988/pydnevnikruapi-extended
"""

from typing import List, Dict, Any
from pydnevnikruapi import AsyncDiaryAPI


class ExtendedDiaryAPI(AsyncDiaryAPI):
    """Расширенный клиент API Дневник.ру"""
    
    # Методы для работы со школой
    async def get_school_groups(self, school_id: int) -> List[Dict[str, Any]]:
        """Все классы школы."""
        return await self._get(f"v1/schools/{school_id}/edu-groups")
    
    async def get_school_persons(self, school_id: int) -> List[Dict[str, Any]]:
        """Все ученики школы."""
        return await self._get(f"v1/schools/{school_id}/persons")
    
    # v2 API методы
    async def get_group_schedule_v2(self, group_id: int, start: str, end: str) -> Dict[str, Any]:
        """Расписание класса (v2 API)."""
        return await self._get(f"v2/edu-groups/{group_id}/lessons/{start}/{end}")
    
    async def get_person_marks_v2(self, person_id: int, start: str, end: str) -> Dict[str, Any]:
        """Оценки ученика (v2 API)."""
        return await self._get(f"v2/persons/{person_id}/marks/{start}/{end}")
    
    # Дополнительные методы
    async def get_group_teachers(self, group_id: int) -> List[Dict[str, Any]]:
        """Учителя класса."""
        return await self._get(f"v1/edu-groups/{group_id}/teachers")
    
    async def get_lesson_attendance(self, lesson_id: int) -> List[Dict[str, Any]]:
        """Посещаемость урока."""
        return await self._get(f"v1/lessons/{lesson_id}/log-entries")
    
    async def get_person_attendance(self, person_id: int, start: str, end: str) -> List[Dict[str, Any]]:
        """Посещаемость ученика за период."""
        return await self._get(f"v1/persons/{person_id}/lesson-log-entries/{start}/{end}")
    
    async def get_group_marks_report(self, group_id: int, start: str, end: str) -> Dict[str, Any]:
        """Отчёт по оценкам класса."""
        return await self._get(f"v1/edu-groups/{group_id}/reporting-period-marks/{start}/{end}")
