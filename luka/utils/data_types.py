from dataclasses import dataclass
from datetime import datetime

@dataclass
class Message:
    role : str
    content : str
    timestamp: datetime

    def __str__(self) -> str:
        lines = self.content.split('\n')
        formatted_datetime = self.timestamp.strftime("%Y%m%d-%H:%M:%S")
        indentation = ' ' * (max(len(self.role), 6) + 2 + len(formatted_datetime) + 3)

        if len(lines) > 1:
            indented_content = ('\n' + indentation).join(lines)
            return f"[{formatted_datetime}] {self.role}: {lines[0]}{indented_content}"
        else:
            return f"[{formatted_datetime}] {self.role}: {self.content}"