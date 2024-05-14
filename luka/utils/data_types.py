from dataclasses import dataclass
from datetime import datetime
import textwrap

@dataclass
class Message:
    role : str
    content : str
    timestamp: datetime

    def __str__(self) -> str:
        lines = [l.strip() for l in self.content.split('\n') if not l.strip().isspace()]
        formatted_datetime = self.timestamp.strftime("%Y%m%d-%H:%M:%S")
        prefix = f"[{formatted_datetime}] {self.role}:"
        wrapper = textwrap.TextWrapper(subsequent_indent='\t', initial_indent=prefix, width=80)

        return wrapper.fill(self.content)