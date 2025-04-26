"""
Progress reporter service for tracking long-running operations.

This module implements the Observer pattern to report progress of
long-running repository analysis operations.
"""

from typing import Protocol, Callable, Optional, Dict, Any
from dataclasses import dataclass


class ProgressObserver(Protocol):
    """Protocol defining the interface for progress observers."""

    def update(self, current: int, total: int, status: Optional[str] = None) -> None:
        """Update the observer with current progress.

        Args:
            current: Current progress value
            total: Total number of items to process
            status: Optional status message
        """
        ...


@dataclass
class ProgressUpdate:
    """Data class representing a progress update."""

    current: int
    total: int
    status: Optional[str] = None


class ProgressReporter:
    """Progress reporter for long-running operations.

    This class implements the Observer pattern to allow multiple clients to
    subscribe to progress updates from the repository analysis process.
    """

    def __init__(self):
        """Initialize the progress reporter."""
        self._observers: list[ProgressObserver] = []
        self._progress_callback: Optional[Callable[[int, int, Optional[str]], None]] = (
            None
        )
        self._current = 0
        self._total = 0
        self._status = None

    def register_observer(self, observer: ProgressObserver) -> None:
        """Register a new observer.

        Args:
            observer: Observer to register
        """
        if observer not in self._observers:
            self._observers.append(observer)

    def remove_observer(self, observer: ProgressObserver) -> None:
        """Remove an observer.

        Args:
            observer: Observer to remove
        """
        if observer in self._observers:
            self._observers.remove(observer)

    def set_progress_callback(
        self, callback: Optional[Callable[[int, int, Optional[str]], None]]
    ) -> None:
        """Set a callback function for progress updates.

        Args:
            callback: Function to call with progress updates
        """
        self._progress_callback = callback

    def update_progress(
        self, current: int, total: int, status: Optional[str] = None
    ) -> None:
        """Update the progress and notify all observers.

        Args:
            current: Current progress value
            total: Total number of items to process
            status: Optional status message
        """
        self._current = current
        self._total = total
        # Ensure status doesn't contain newlines that could disrupt console output
        if status:
            self._status = status.replace("\n", " ")
        else:
            self._status = status

        # Notify all observers
        for observer in self._observers:
            observer.update(current, total, self._status)

        # Call the callback if set
        if self._progress_callback:
            self._progress_callback(current, total, self._status)

    def increment(self, amount: int = 1, status: Optional[str] = None) -> None:
        """Increment the progress value.

        Args:
            amount: Amount to increment by
            status: Optional status message
        """
        self.update_progress(self._current + amount, self._total, status)

    def get_progress(self) -> ProgressUpdate:
        """Get the current progress.

        Returns:
            Current progress update
        """
        return ProgressUpdate(self._current, self._total, self._status)
