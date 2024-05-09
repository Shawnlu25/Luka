from abc import ABC, abstractmethod
from datetime import datetime

from whoosh.fields import Schema, TEXT, DATETIME, KEYWORD
from whoosh.filedb.filestore import RamStorage
from whoosh.index import create_in
from whoosh.qparser import QueryParser
from whoosh.query import DateRange

from luka.utils import Message

# Adapted from https://github.com/cpacker/MemGPT/blob/main/memgpt/memory.py
class RecallMemory(ABC):
    @abstractmethod
    def text_search(self, query_string, start=None, limit=None):
        pass

    @abstractmethod
    def date_search(self, start_date, end_date, start=None, limit=None):
        pass

    @abstractmethod
    def __repr__(self) -> str:
        pass

    @abstractmethod
    def insert(self, message: Message):
        pass

class TransientRecallMemory(RecallMemory):
    """
    A RecallMemory implementation that stores messages in RAM, powered by Whoosh.
    """
    def __init__(self):
        self._schema = Schema(role=KEYWORD(stored=True), content=TEXT(stored=True), timestamp=DATETIME(stored=True))
        self._index = RamStorage().create_index(self._schema)
    
    def reset(self):
        self._index = RamStorage().create_index(self._schema)

    def text_search(self, query_string:str, start:int = 0, limit:int = 5):
        with self._index.searcher() as searcher:
            query = QueryParser("content", self._index.schema).parse(query_string)
            results = searcher.search(query, limit=limit*(start+1))
            results = results[start*limit:]
            return [Message(content=x["content"], role=x["role"], timestamp=x["timestamp"]) for x in [dict(result) for result in results]]

    def date_search(self, start_date: datetime, end_date: datetime, start:int = 0, limit:int = 5):
        with self._index.searcher() as searcher:
            query = DateRange("timestamp", start_date, end_date, startexcl=False, endexcl=False)
            results = searcher.search(query, limit=limit*(start+1), sortedby="timestamp")
            results = results[start*limit:]
            return [Message(content=x["content"], role=x["role"], timestamp=x["timestamp"]) for x in [dict(result) for result in results]]

    def __repr__(self) -> str:
        pass

    def __len__(self):
        with self._index.searcher() as searcher:
            return searcher.doc_count()

    def insert(self, message: Message):
        with self._index.writer() as writer:
            writer.add_document(role=message.role, content=message.content, timestamp=message.timestamp)