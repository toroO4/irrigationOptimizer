"""
Service — Irrigation Operations.

Orchestrates irrigation schedule generation using the scheduling engine.
"""

from typing import Any, Dict, List

from app.core.logging_config import get_logger
from app.scheduling.engine import IrrigationScheduler

logger = get_logger(__name__)


class IrrigationService:
    """Manages irrigation schedule generation and retrieval."""

    def __init__(self):
        self.scheduler = IrrigationScheduler()
        self.schedule_history: List[Dict[str, Any]] = []

    async def generate_plan(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate an irrigation plan for a single field.

        Args:
            params: Field parameters matching IrrigationPlanRequest fields.

        Returns:
            Generated irrigation schedule.
        """
        schedule = self.scheduler.generate_schedule(**params)
        self.schedule_history.append(schedule)
        return schedule

    async def generate_multi_field_plan(self, fields: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate plans for multiple fields."""
        plan = self.scheduler.generate_multi_field_plan(fields)
        self.schedule_history.extend(plan["schedules"])
        return plan

    def get_schedules(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent schedule history."""
        return self.schedule_history[-limit:]

    def get_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get full schedule history."""
        return list(reversed(self.schedule_history[-limit:]))


# Singleton
irrigation_service = IrrigationService()
