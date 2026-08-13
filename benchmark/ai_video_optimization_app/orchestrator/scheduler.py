"""Scheduler module for managing experiment execution order.

Provides placeholder scheduling infrastructure for future multi-worker support.
"""

from __future__ import annotations

from loguru import logger


class Scheduler:
    """Experiment scheduler.

    Manages the queue of experiments to be processed. Currently uses a
    simple FIFO approach; future versions may support priority queues
    and distributed workers.
    """

    def __init__(self) -> None:
        """Initialize the scheduler."""
        self._queue: list[str] = []
        logger.info("Scheduler initialized")

    def enqueue(self, experiment_id: str) -> None:
        """Add an experiment to the processing queue.

        Args:
            experiment_id: ID of the experiment to enqueue.
        """
        if experiment_id not in self._queue:
            self._queue.append(experiment_id)
            logger.info(f"Experiment enqueued: {experiment_id}")

    def dequeue(self) -> str | None:
        """Remove and return the next experiment ID from the queue.

        Returns:
            The next experiment ID, or None if queue is empty.
        """
        if not self._queue:
            return None
        exp_id = self._queue.pop(0)
        logger.info(f"Experiment dequeued: {exp_id}")
        return exp_id

    def is_empty(self) -> bool:
        """Check if the queue is empty.

        Returns:
            True if no experiments are queued.
        """
        return len(self._queue) == 0

    @property
    def size(self) -> int:
        """Number of experiments in the queue."""
        return len(self._queue)