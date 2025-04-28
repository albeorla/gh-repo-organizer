import pytest
import asyncio
from src.repo_organizer.domain.core.events import DomainEvent, EventDispatcher
from dataclasses import dataclass
import uuid
from datetime import datetime


# --- Test Event Classes ---
@dataclass(frozen=True)
class TestEventData(DomainEvent):
    value: int = 0

    def _get_event_data(self):
        return {"value": self.value}


# --- Fixtures ---
@pytest.fixture
def dispatcher():
    return EventDispatcher()


# --- Tests ---
def test_event_creation():
    event = TestEventData(aggregate_id="agg-1", value=42)
    assert isinstance(event.event_id, uuid.UUID)
    assert isinstance(event.timestamp, datetime)
    assert event.aggregate_id == "agg-1"
    assert event.value == 42
    d = event.to_dict()
    assert d["event_type"] == "TestEventData"
    assert d["data"] == {"value": 42}


def test_sync_handler_dispatch(dispatcher):
    called = {}

    def handler(event):
        called["event"] = event

    dispatcher.register(TestEventData, handler)
    event = TestEventData(aggregate_id="agg-2", value=99)
    asyncio.run(dispatcher.dispatch(event))
    assert called["event"] == event


def test_async_handler_dispatch(dispatcher):
    called = {}

    async def handler(event):
        called["event"] = event

    dispatcher.register(TestEventData, handler)
    event = TestEventData(aggregate_id="agg-3", value=123)
    asyncio.run(dispatcher.dispatch(event))
    assert called["event"] == event


def test_mixed_handlers(dispatcher):
    called = {"sync": False, "async": False}

    def sync_handler(event):
        called["sync"] = True

    async def async_handler(event):
        called["async"] = True

    dispatcher.register(TestEventData, sync_handler)
    dispatcher.register(TestEventData, async_handler)
    event = TestEventData(aggregate_id="agg-4", value=7)
    asyncio.run(dispatcher.dispatch(event))
    assert called["sync"] and called["async"]


def test_unregister_handler(dispatcher):
    called = {"sync": False}

    def sync_handler(event):
        called["sync"] = True

    dispatcher.register(TestEventData, sync_handler)
    dispatcher.unregister(TestEventData, sync_handler)
    event = TestEventData(aggregate_id="agg-5", value=0)
    asyncio.run(dispatcher.dispatch(event))
    assert not called["sync"]


def test_no_handlers(dispatcher):
    event = TestEventData(aggregate_id="agg-6", value=0)
    # Should not raise
    asyncio.run(dispatcher.dispatch(event))
