from dataclasses import dataclass
from datetime import datetime


@dataclass
class File:
    name: str
    path: str
    size: int
    modified: datetime
    is_dir: bool
