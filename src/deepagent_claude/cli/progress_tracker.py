"""Progress tracking for long-running operations"""

from typing import Dict, Any, Optional
from rich.progress import Progress, TaskID, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn

class ProgressTracker:
    """
    Tracks progress of multiple concurrent tasks

    Uses Rich progress bars for visual feedback on task completion.
    """

    def __init__(self):
        """Initialize progress tracker"""
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
        )
        self._tasks: Dict[TaskID, Dict[str, Any]] = {}
        self._started = False

    def add_task(self, description: str, total: float = 100.0) -> TaskID:
        """
        Add a new task to track

        Args:
            description: Task description
            total: Total units of work

        Returns:
            Task ID for updating progress
        """
        if not self._started:
            self._progress.start()
            self._started = True

        task_id = self._progress.add_task(description, total=total)
        self._tasks[task_id] = {
            "description": description,
            "total": total,
            "completed": 0.0
        }
        return task_id

    def update(self, task_id: TaskID, advance: float = 1.0) -> None:
        """
        Update task progress

        Args:
            task_id: Task ID to update
            advance: Amount to advance progress
        """
        if task_id in self._tasks:
            self._tasks[task_id]["completed"] += advance
            self._progress.update(task_id, advance=advance)

    def complete(self, task_id: TaskID) -> None:
        """
        Mark task as complete

        Args:
            task_id: Task ID to complete
        """
        if task_id in self._tasks:
            task_info = self._tasks[task_id]
            remaining = task_info["total"] - task_info["completed"]
            if remaining > 0:
                self._progress.update(task_id, advance=remaining)
            self._tasks[task_id]["completed"] = task_info["total"]

    def get_status(self) -> Dict[str, Any]:
        """
        Get current tracker status

        Returns:
            Dictionary with status information
        """
        return {
            "tasks": {
                task_id: {
                    "description": info["description"],
                    "total": info["total"],
                    "completed": info["completed"],
                    "percentage": (info["completed"] / info["total"] * 100)
                    if info["total"] > 0 else 0
                }
                for task_id, info in self._tasks.items()
            }
        }

    def stop(self) -> None:
        """Stop the progress display"""
        if self._started:
            self._progress.stop()
            self._started = False
