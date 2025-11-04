import dataclasses
import enum
from typing import Callable


class EventStatus(enum.Enum):
    ONGOING = "ONGOING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclasses.dataclass
class CommandEvent:
    name: str
    func: Callable
    status: str = EventStatus.ONGOING
    code: int = 1  # 1 for success or 0 for failed

    def _set_status(self, status: str) -> None:
        self.status = status

    def _get_status(self) -> str:
        return self.status

    def __repr__(self):
        pass
