import asyncio
import inspect
import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


# --- Base Domain Event ---
@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events in the system."""

    aggregate_id: str
    event_id: uuid.UUID = field(default_factory=uuid.uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary representation for serialization."""
        return {
            "event_id": str(self.event_id),
            "event_type": self.__class__.__name__,
            "timestamp": self.timestamp.isoformat(),
            "aggregate_id": self.aggregate_id,
            "data": self._get_event_data(),
        }

    def _get_event_data(self) -> dict[str, Any]:
        """Extract event-specific data for serialization. Override in subclasses."""
        return {}


# --- Event Dispatcher ---
HandlerFunc = Callable[[DomainEvent], Any]
AsyncHandlerFunc = Callable[[DomainEvent], Any]


class EventDispatcher:
    """Dispatches events to registered handlers. Supports both sync and async handlers."""

    def __init__(self):
        self._handlers: dict[
            type[DomainEvent],
            list[HandlerFunc | AsyncHandlerFunc],
        ] = {}
        self._logger = logging.getLogger(__name__)

    def register(
        self,
        event_type: type[DomainEvent],
        handler: HandlerFunc | AsyncHandlerFunc,
    ) -> None:
        """Register a handler for a specific event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)
            self._logger.debug(
                f"Registered handler {handler.__name__} for {event_type.__name__}",
            )

    def unregister(
        self,
        event_type: type[DomainEvent],
        handler: HandlerFunc | AsyncHandlerFunc,
    ) -> None:
        """Unregister a handler for a specific event type."""
        if event_type in self._handlers and handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            self._logger.debug(
                f"Unregistered handler {handler.__name__} for {event_type.__name__}",
            )

    async def dispatch(self, event: DomainEvent) -> None:
        """Dispatch an event to all registered handlers (sync and async)."""
        event_type = type(event)
        handlers = self._get_handlers_for_event(event)
        if not handlers:
            self._logger.warning(f"No handlers registered for {event_type.__name__}")
            return
        self._logger.debug(
            f"Dispatching {event_type.__name__} to {len(handlers)} handlers",
        )
        sync_tasks = []
        async_tasks = []
        for handler in handlers:
            if inspect.iscoroutinefunction(handler):
                async_tasks.append(handler(event))
            else:
                sync_tasks.append(handler(event))
        # Run synchronous handlers
        for _task in sync_tasks:
            pass  # Already executed
        # Run asynchronous handlers
        if async_tasks:
            await asyncio.gather(*async_tasks)

    def _get_handlers_for_event(
        self,
        event: DomainEvent,
    ) -> list[HandlerFunc | AsyncHandlerFunc]:
        """Get all handlers for an event, including parent class handlers."""
        event_type = type(event)
        handlers: set[HandlerFunc | AsyncHandlerFunc] = set()
        for registered_type, type_handlers in self._handlers.items():
            if issubclass(event_type, registered_type):
                handlers.update(type_handlers)
        return list(handlers)


# --- Global Event Bus Singleton ---
event_bus = EventDispatcher()

"""
USAGE EXAMPLE:

from src.repo_organizer.domain.core.events import DomainEvent, event_bus

# Define a custom event
@dataclass(frozen=True)
class MyEvent(DomainEvent):
    value: int
    def _get_event_data(self):
        return {"value": self.value}

# Define a handler
async def my_handler(event: MyEvent):
    print(f"Handled event: {event}")

# Register handler
event_bus.register(MyEvent, my_handler)

# Dispatch event
import asyncio
asyncio.run(event_bus.dispatch(MyEvent(aggregate_id="123", value=42)))
"""
