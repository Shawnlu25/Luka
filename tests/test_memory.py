import pytest

from luka.memory.recall_mem import TransientRecallMemory
from luka.memory.working_mem import FIFOConversationMemory
from luka.memory.working_mem import TextEditorMemory
from luka.utils import Message
from datetime import datetime

_SUMMARY = "THIS IS A SUMMARY"

@pytest.fixture(scope="module")
def transient_mem():
    return TransientRecallMemory()

@pytest.fixture(scope="module")
def fifo_mem():
    def dummy_tokenize(x):
        return x.split(" ")
    
    def dummy_summarize(x):
        return _SUMMARY

    return FIFOConversationMemory(tokenize=dummy_tokenize, summarize=dummy_summarize, max_size=30, trigger_threshold=0.8, target_threshold=0.5)

@pytest.fixture(scope="module")
def text_mem():
    def dummy_tokenize(x):
        return x.split(" ")
    return TextEditorMemory(tokenize=dummy_tokenize)


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
    assert len(transient_mem) == 0, "TransientRecallMemory should have 0 messages"

def test_fifo_conversation_memory(fifo_mem):
    fifo_mem.insert(Message(role="user", content="Lorem ipsum dolor sit amet, consectetur adipiscing elit.", timestamp=datetime(2024, 5, 1, 15, 30, 0)))
    messages = fifo_mem._message_queue
    assert len(messages) == 1, "FIFOConversationMemory: message queue should have 1 message"
    assert messages[0][0].content == "Lorem ipsum dolor sit amet, consectetur adipiscing elit.", "FIFOConversationMemory: message content should match"
    
    fifo_mem.insert(Message(role="user", content="Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.", timestamp=datetime(2024, 5, 1, 15, 30, 10)))
    messages = fifo_mem._message_queue
    assert len(messages) == 2, "FIFOConversationMemory: message queue should have 2 messages"
    assert messages[0][0].content == "Lorem ipsum dolor sit amet, consectetur adipiscing elit.", "FIFOConversationMemory: message content should match"
    assert messages[1][0].content == "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.", "FIFOConversationMemory: message content should match"
    fifo_mem.insert(Message(role="user", content="Ut enim ad minim veniam", timestamp=datetime(2024, 5, 1, 15, 30, 20)))
    messages = fifo_mem._message_queue
    
    assert len(messages) == 2, "FIFOConversationMemory: message queue should have 2 messages"
    assert messages[0][0].content == _SUMMARY, "FIFOConversationMemory: first message should be a summary"
    assert messages[1][0].content == "Ut enim ad minim veniam", "FIFOConversationMemory: second message should be the latest inserted message"

    fifo_mem.replace(Message(role="user", content="Vale.", timestamp=datetime(2024, 5, 1, 15, 30, 20)), 1)
    messages = fifo_mem._message_queue
    assert len(messages) == 2, "FIFOConversationMemory: message queue should have 2 messages"
    assert messages[0][0].content == _SUMMARY, "FIFOConversationMemory: first message should be a summary"
    assert messages[1][0].content == "Vale.", "FIFOConversationMemory: second message should be the latest inserted message"

    assert str(fifo_mem)
    fifo_mem.reset()
    assert len(fifo_mem._message_queue) == 0, "FIFOConversationMemory: message queue should be empty after reset"

def test_text_editor_memory(text_mem):
    text_mem.insert("Lorem ipsum dolor sit amet, consectetur adipiscing elit.", -1)
    text_mem.insert("Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.", 0)
    printed = text_mem.__repr__()
    assert printed == "1: Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.\n2: Lorem ipsum dolor sit amet, consectetur adipiscing elit.\n", "TextEditorMemory: printed text should have line numbers"

    text_mem.replace("Ut enim ad minim veniam\nLorem ipsum dolor sit amet, consectetur adipiscing elit.\n    aliquip ex ea commodo consequat.", (-2,0))
    printed = text_mem.__repr__()
    assert printed == "1: Ut enim ad minim veniam\n2: Lorem ipsum dolor sit amet, consectetur adipiscing elit.\n3: aliquip ex ea commodo consequat.\n", "TextEditorMemory: replaced string should have 3 lines"