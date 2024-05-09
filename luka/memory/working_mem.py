from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from luka.utils import Message

class WorkingMemory(ABC):
    @abstractmethod
    def insert(self, record: Any):
        """Insert message into working memory"""
    
    @abstractmethod
    def reset(self):
        """Reset working memory"""

    @abstractmethod
    def __repr__(self) -> str:
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
    
    def insert(self, record: Message):
        self._message_queue.append((record, self._tokenize(str(record))))
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
        self._message_queue.insert(0, (summary_msg, self._tokenize(str(summary_msg))))
    
    def __repr__(self) -> str:
        return "\n".join([str(msg) for msg, _ in self._message_queue])
    
    