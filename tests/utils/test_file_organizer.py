from pathlib import Path

from deepagent_coder.utils.file_organizer import FileOrganizer


def test_file_organizer_initialization(tmp_path):
    organizer = FileOrganizer(base_path=str(tmp_path))
    assert organizer is not None
    assert Path(organizer.base_path).exists()


def test_create_standard_structure(tmp_path):
    organizer = FileOrganizer(base_path=str(tmp_path))
    organizer.create_standard_structure()

    assert (Path(tmp_path) / "sessions").exists()
    assert (Path(tmp_path) / "decisions").exists()
    assert (Path(tmp_path) / "summaries").exists()


def test_save_and_load_session_data(tmp_path):
    organizer = FileOrganizer(base_path=str(tmp_path))
    session_data = {"user": "test", "timestamp": "2024"}

    path = organizer.save_session_data("test_session", session_data)
    assert path.exists()

    loaded = organizer.load_session_data("test_session")
    assert loaded["user"] == "test"
