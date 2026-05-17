"""
Pydantic Schemas — Background Tasks.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel

class TaskResponse(BaseModel):
    """Response when a background task is triggered."""
    task_id: str
    message: str
    
class TaskStatusResponse(BaseModel):
    """Response when polling task status."""
    task_id: str
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None
