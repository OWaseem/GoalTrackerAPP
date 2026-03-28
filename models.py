from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Goal:
    id: int
    title: str
    description: str
    category: str
    due_date: Optional[date]
    status: str  # "pending" or "done"
    created_at: str
