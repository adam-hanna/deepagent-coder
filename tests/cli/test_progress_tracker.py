# tests/cli/test_progress_tracker.py
from deepagent_claude.cli.progress_tracker import ProgressTracker


def test_progress_tracker_creation():
    """Test creating progress tracker"""
    tracker = ProgressTracker()
    assert tracker is not None


def test_progress_tracker_add_task():
    """Test adding task to tracker"""
    tracker = ProgressTracker()
    task_id = tracker.add_task("Test task", total=100)
    assert task_id is not None


def test_progress_tracker_update_task():
    """Test updating task progress"""
    tracker = ProgressTracker()
    task_id = tracker.add_task("Test task", total=100)
    tracker.update(task_id, advance=50)
    # Should not raise exception


def test_progress_tracker_complete_task():
    """Test completing a task"""
    tracker = ProgressTracker()
    task_id = tracker.add_task("Test task", total=100)
    tracker.complete(task_id)
    # Should not raise exception


def test_progress_tracker_get_status():
    """Test getting tracker status"""
    tracker = ProgressTracker()
    task_id = tracker.add_task("Test task", total=100)
    status = tracker.get_status()
    assert isinstance(status, dict)
    assert "tasks" in status
