from abc import ABC, abstractmethod
from typing import Any, Tuple

from luka.utils import Message

import textwrap

class WorkingMemory(ABC):
    @abstractmethod
    def insert(self, record: Any, pos: Any):  # pragma: no cover
        """Insert a record into working memory at position"""
    
    @abstractmethod
    def replace(self, record: Any, pos: Any):  # pragma: no cover
        """Replace the record at specified position with new record"""

    @abstractmethod
    def reset(self):  # pragma: no cover
        """Reset working memory"""

    @abstractmethod
    def __repr__(self) -> str:  # pragma: no cover
        pass

class FIFOConversationMemory(WorkingMemory):
    def __init__(self, tokenize, summarize, max_size=2048, trigger_threshold=0.8, target_threshold=0.5):
        self._message_queue = []
        self._current_size = 0

        self._tokenize = tokenize
        self._summarize = summarize

        self._max_size = max_size
        self._trigger_threshold = trigger_threshold
        self._target_threshold = target_threshold
        assert self._trigger_threshold > self._target_threshold > 0, "Trigger threshold must be greater than target threshold, and both must be greater than 0."
    
    def reset(self):
        self._message_queue = []
        self._current_size = 0
    
    def insert(self, record: Message, pos=None):
        self._message_queue.append((record, len(self._tokenize(str(record)))))
        self._current_size += self._message_queue[-1][1]

        if self._current_size < self._max_size * self._trigger_threshold:
            return
        
        popped_messages = []
        while self._current_size > self._max_size * self._target_threshold:
            msg, msg_size = self._message_queue.pop(0)
            popped_messages.append(msg)
            self._current_size -= msg_size
        
        if len(popped_messages) == 0:
            return
        
        summary = self._summarize(popped_messages)
        summary_msg = Message(content=summary, role="system", timestamp=popped_messages[-1].timestamp)
        self._message_queue.insert(0, (summary_msg, len(self._tokenize(str(summary_msg)))))
    
    def replace(self, record: Message, pos: int):
        # check if pos is valid
        if pos <= 0 or pos >= len(self._message_queue):
            raise ValueError(f"Invalid position {pos} for replacement.")
        self._current_size -= self._message_queue[pos][1]
        self._message_queue[pos] = (record, len(self._tokenize(str(record))))
        self._current_size += self._message_queue[pos][1]

    def __repr__(self) -> str:
        return "\n".join([str(msg) for msg, _ in self._message_queue])
    

class TextEditorMemory(WorkingMemory):
    def __init__(self, tokenize, max_size=2048):
        self._lines = []
        self._current_size = 0

        self._tokenize = tokenize
        self._max_size = max_size
    
    def reset(self):
        self._lines = []
        self._current_size = 0
    
    def insert(self, record: str, pos: int = -1):
        new_lines = [(l.strip(), len(self._tokenize(l))) for l in record.split("\n")]
        if pos == -1:
            pos = len(self._lines)
        for line in new_lines:
            self._lines.insert(pos, line)
            self._current_size += line[1]
            pos += 1
    
    def replace(self, record: str, pos: Tuple[int, int]):
        if pos[0] > pos[1] or pos[0] * pos[1] < 0:
            raise ValueError(f"Invalid position {pos} for replacement.")
        if pos[0] < 0 and pos[1] <= 0:
            pos = (pos[0] + len(self._lines), pos[1] + len(self._lines))
        
        for line in self._lines[pos[0]:pos[1]]:
            self._current_size -= line[1]
        del self._lines[pos[0]:pos[1]]

        self.insert(record, pos[0])


    def __repr__(self) -> str:
        num_width = len(str(len(self._lines)))  # Calculate the width needed for line numbers
        result = ""

        wrapper = textwrap.TextWrapper(subsequent_indent='\t', width=80)
        for i, line in enumerate(self._lines, start=1):
            line_num = str(i).rjust(num_width)  # Right-align line numbers
            result += wrapper.fill(f"{line_num}| {line[0]}") + "\n"
        
        return result
        
        
        
        