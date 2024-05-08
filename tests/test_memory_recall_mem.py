import pytest

from luka.memory.recall_mem import TransientRecallMemory
from luka.utils import Message
from datetime import datetime

@pytest.fixture(scope="module")
def transient_mem():
    return TransientRecallMemory()

def test_transient_recall_memory_insert(transient_mem):
    transient_mem.insert(Message(role="user", content="Hello", timestamp=datetime(2024, 5, 1, 15, 30, 0)))
    transient_mem.insert(Message(role="agent", content="World", timestamp=datetime(2024, 5, 1, 15, 35, 0)))
    transient_mem.insert(Message(role="user", content="Hello. How is the weather?", timestamp=datetime(2024, 5, 1, 15, 35, 30)))
    transient_mem.insert(Message(role="agent", content="Great", timestamp=datetime(2024, 5, 1, 15, 35, 30)))
    assert len(transient_mem) == 4, "TransientRecallMemory should have 4 messages"
    transient_mem.reset()

def test_transient_recall_memory_text_search(transient_mem):
    transient_mem.insert(Message(role="user", content="Hello", timestamp=datetime(2024, 5, 1, 15, 30, 0)))
    transient_mem.insert(Message(role="agent", content="World", timestamp=datetime(2024, 5, 1, 15, 35, 0)))
    transient_mem.insert(Message(role="user", content="Hello. How is the weather?", timestamp=datetime(2024, 5, 1, 15, 35, 30)))
    transient_mem.insert(Message(role="agent", content="Great", timestamp=datetime(2024, 5, 1, 15, 35, 30)))

    messages = transient_mem.text_search("weather")
    assert isinstance(messages[0], Message), "TransientRecallMemory: text_search should return a list of Message objects"
    assert len(messages) == 1, "TransientRecallMemory: searching for `weather` should return 1 message"

    messages = transient_mem.text_search("HELLO")
    assert len(messages) == 2, "TransientRecallMemory: searching for `HELLO` should return 2 messages"

    messages = transient_mem.text_search("HELLO", start=12, limit=1)
    assert len(messages) == 0, "TransientRecallMemory: searching for `HELLO` with `limit=1 start=12` should return 0 message"

    messages = transient_mem.text_search("HELLO", start=1, limit=1)
    assert len(messages) == 1, "TransientRecallMemory: searching for `HELLO` with `limit=1 start=1` should return 1 message"

    messages = transient_mem.text_search("six flags!")
    assert len(messages) == 0, "TransientRecallMemory: searching for `six flags!` should return 0 message"

    transient_mem.reset()

def test_transient_recall_memory_date_search(transient_mem):
    transient_mem.insert(Message(role="user", content="Hello", timestamp=datetime(2024, 5, 1, 15, 30, 0)))
    transient_mem.insert(Message(role="agent", content="World", timestamp=datetime(2024, 5, 12, 15, 35, 0)))
    transient_mem.insert(Message(role="user", content="Hello. How is the weather?", timestamp=datetime(2024, 5, 13, 15, 35, 30)))
    transient_mem.insert(Message(role="agent", content="Great", timestamp=datetime(2024, 5, 13, 15, 35, 35)))

    messages = transient_mem.date_search(datetime(2024, 5, 12), datetime(2024, 5, 13))
    assert isinstance(messages[0], Message), "TransientRecallMemory: date_search should return a list of Message objects"
    assert len(messages) == 1, "TransientRecallMemory: searching for messages between 2024-05-12 and 2024-05-13 should return 1 message"

    messages = transient_mem.date_search(datetime(2024, 5, 12), datetime(2024, 5, 14))
    assert isinstance(messages[0], Message), "TransientRecallMemory: date_search should return a list of Message objects"
    assert len(messages) == 3, "TransientRecallMemory: searching for messages between 2024-05-12 and 2024-05-13 should return 3 messages"
    assert messages[0].timestamp < messages[1].timestamp < messages[2].timestamp, "TransientRecallMemory: messages should be sorted by timestamp"

    transient_mem.reset()

