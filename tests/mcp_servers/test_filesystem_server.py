# tests/mcp_servers/test_filesystem_server.py
"""Comprehensive tests for filesystem operations MCP server"""

import os
from pathlib import Path

import pytest

from deepagent_coder.mcp_servers.filesystem_server import (
    _create_directory_impl,
    _delete_directory_impl,
    _delete_file_impl,
    _get_file_info_impl,
    _list_directory_impl,
    _move_file_impl,
    _read_file_impl,
    _write_file_impl,
)

# ============================================================================
# write_file tests
# ============================================================================


@pytest.mark.asyncio
async def test_write_file_simple(tmp_path):
    """Test writing a simple file"""
    file_path = tmp_path / "test.txt"
    content = "Hello World"

    result = await _write_file_impl(str(file_path), content)

    assert result["success"] is True
    assert result["size"] == len(content)
    assert file_path.exists()
    assert file_path.read_text() == content


@pytest.mark.asyncio
async def test_write_file_creates_parent_dirs(tmp_path):
    """Test that write_file creates parent directories if needed"""
    file_path = tmp_path / "subdir" / "nested" / "test.txt"
    content = "Test content"

    result = await _write_file_impl(str(file_path), content)

    assert result["success"] is True
    assert file_path.exists()
    assert file_path.read_text() == content


@pytest.mark.asyncio
async def test_write_file_overwrites_existing(tmp_path):
    """Test that write_file overwrites existing files"""
    file_path = tmp_path / "test.txt"
    file_path.write_text("Old content")

    result = await _write_file_impl(str(file_path), "New content")

    assert result["success"] is True
    assert file_path.read_text() == "New content"


@pytest.mark.asyncio
async def test_write_file_empty_content(tmp_path):
    """Test writing an empty file"""
    file_path = tmp_path / "empty.txt"

    result = await _write_file_impl(str(file_path), "")

    assert result["success"] is True
    assert result["size"] == 0
    assert file_path.exists()
    assert file_path.read_text() == ""


@pytest.mark.asyncio
async def test_write_file_unicode_content(tmp_path):
    """Test writing unicode content"""
    file_path = tmp_path / "unicode.txt"
    content = "Hello 世界 🌍"

    result = await _write_file_impl(str(file_path), content)

    assert result["success"] is True
    assert file_path.read_text(encoding="utf-8") == content


# ============================================================================
# read_file tests
# ============================================================================


@pytest.mark.asyncio
async def test_read_file_simple(tmp_path):
    """Test reading a simple file"""
    file_path = tmp_path / "test.txt"
    content = "Hello World"
    file_path.write_text(content)

    result = await _read_file_impl(str(file_path))

    assert result["success"] is True
    assert result["content"] == content
    assert result["size"] == len(content)
    assert "modified" in result


@pytest.mark.asyncio
async def test_read_file_not_found(tmp_path):
    """Test reading a non-existent file"""
    file_path = tmp_path / "nonexistent.txt"

    result = await _read_file_impl(str(file_path))

    assert "error" in result
    assert "not found" in result["error"].lower()


@pytest.mark.asyncio
async def test_read_file_directory(tmp_path):
    """Test reading a directory (should fail)"""
    dir_path = tmp_path / "testdir"
    dir_path.mkdir()

    result = await _read_file_impl(str(dir_path))

    assert "error" in result
    assert "not a file" in result["error"].lower()


@pytest.mark.asyncio
async def test_read_file_empty(tmp_path):
    """Test reading an empty file"""
    file_path = tmp_path / "empty.txt"
    file_path.write_text("")

    result = await _read_file_impl(str(file_path))

    assert result["success"] is True
    assert result["content"] == ""
    assert result["size"] == 0


@pytest.mark.asyncio
async def test_read_file_unicode(tmp_path):
    """Test reading unicode content"""
    file_path = tmp_path / "unicode.txt"
    content = "Hello 世界 🌍"
    file_path.write_text(content, encoding="utf-8")

    result = await _read_file_impl(str(file_path))

    assert result["success"] is True
    assert result["content"] == content


# ============================================================================
# list_directory tests
# ============================================================================


@pytest.mark.asyncio
async def test_list_directory_simple(tmp_path):
    """Test listing a directory with files"""
    (tmp_path / "file1.txt").write_text("content1")
    (tmp_path / "file2.txt").write_text("content2")
    (tmp_path / "subdir").mkdir()

    result = await _list_directory_impl(str(tmp_path))

    assert result["success"] is True
    assert result["count"] == 3
    assert len(result["entries"]) == 3

    # Check entries contain expected fields
    for entry in result["entries"]:
        assert "name" in entry
        assert "path" in entry
        assert "type" in entry
        assert "modified" in entry


@pytest.mark.asyncio
async def test_list_directory_empty(tmp_path):
    """Test listing an empty directory"""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    result = await _list_directory_impl(str(empty_dir))

    assert result["success"] is True
    assert result["count"] == 0
    assert result["entries"] == []


@pytest.mark.asyncio
async def test_list_directory_not_found(tmp_path):
    """Test listing a non-existent directory"""
    dir_path = tmp_path / "nonexistent"

    result = await _list_directory_impl(str(dir_path))

    assert "error" in result
    assert "not found" in result["error"].lower()


@pytest.mark.asyncio
async def test_list_directory_is_file(tmp_path):
    """Test listing a file (should fail)"""
    file_path = tmp_path / "test.txt"
    file_path.write_text("content")

    result = await _list_directory_impl(str(file_path))

    assert "error" in result
    assert "not a directory" in result["error"].lower()


@pytest.mark.asyncio
async def test_list_directory_sorting(tmp_path):
    """Test that directories are listed before files, alphabetically"""
    (tmp_path / "zebra.txt").write_text("content")
    (tmp_path / "alpha.txt").write_text("content")
    (tmp_path / "zoo").mkdir()
    (tmp_path / "aaa").mkdir()

    result = await _list_directory_impl(str(tmp_path))

    assert result["success"] is True
    names = [entry["name"] for entry in result["entries"]]
    # Directories should come first
    assert names[0] == "aaa"
    assert names[1] == "zoo"
    # Then files
    assert names[2] == "alpha.txt"
    assert names[3] == "zebra.txt"


# ============================================================================
# create_directory tests
# ============================================================================


@pytest.mark.asyncio
async def test_create_directory_simple(tmp_path):
    """Test creating a simple directory"""
    dir_path = tmp_path / "newdir"

    result = await _create_directory_impl(str(dir_path))

    assert result["success"] is True
    assert dir_path.exists()
    assert dir_path.is_dir()


@pytest.mark.asyncio
async def test_create_directory_nested(tmp_path):
    """Test creating nested directories"""
    dir_path = tmp_path / "level1" / "level2" / "level3"

    result = await _create_directory_impl(str(dir_path))

    assert result["success"] is True
    assert dir_path.exists()
    assert dir_path.is_dir()


@pytest.mark.asyncio
async def test_create_directory_already_exists(tmp_path):
    """Test creating a directory that already exists (should succeed)"""
    dir_path = tmp_path / "existing"
    dir_path.mkdir()

    result = await _create_directory_impl(str(dir_path))

    assert result["success"] is True
    assert "already exists" in result["message"].lower()


@pytest.mark.asyncio
async def test_create_directory_file_exists(tmp_path):
    """Test creating a directory where a file with that name exists"""
    file_path = tmp_path / "test.txt"
    file_path.write_text("content")

    result = await _create_directory_impl(str(file_path))

    assert "error" in result
    assert "not a directory" in result["error"].lower()


# ============================================================================
# move_file tests
# ============================================================================


@pytest.mark.asyncio
async def test_move_file_simple(tmp_path):
    """Test moving a file"""
    source = tmp_path / "source.txt"
    dest = tmp_path / "dest.txt"
    source.write_text("content")

    result = await _move_file_impl(str(source), str(dest))

    assert result["success"] is True
    assert not source.exists()
    assert dest.exists()
    assert dest.read_text() == "content"


@pytest.mark.asyncio
async def test_move_file_to_subdir(tmp_path):
    """Test moving a file to a subdirectory"""
    source = tmp_path / "file.txt"
    dest_dir = tmp_path / "subdir"
    dest_dir.mkdir()
    dest = dest_dir / "file.txt"
    source.write_text("content")

    result = await _move_file_impl(str(source), str(dest))

    assert result["success"] is True
    assert not source.exists()
    assert dest.exists()


@pytest.mark.asyncio
async def test_move_file_creates_parent_dirs(tmp_path):
    """Test that move_file creates parent directories if needed"""
    source = tmp_path / "file.txt"
    dest = tmp_path / "new" / "nested" / "file.txt"
    source.write_text("content")

    result = await _move_file_impl(str(source), str(dest))

    assert result["success"] is True
    assert dest.exists()
    assert dest.read_text() == "content"


@pytest.mark.asyncio
async def test_move_file_source_not_found(tmp_path):
    """Test moving a non-existent file"""
    source = tmp_path / "nonexistent.txt"
    dest = tmp_path / "dest.txt"

    result = await _move_file_impl(str(source), str(dest))

    assert "error" in result
    assert "not found" in result["error"].lower()


@pytest.mark.asyncio
async def test_move_file_dest_exists(tmp_path):
    """Test moving to a destination that already exists"""
    source = tmp_path / "source.txt"
    dest = tmp_path / "dest.txt"
    source.write_text("source content")
    dest.write_text("dest content")

    result = await _move_file_impl(str(source), str(dest))

    assert "error" in result
    assert "already exists" in result["error"].lower()


@pytest.mark.asyncio
async def test_move_directory(tmp_path):
    """Test moving a directory"""
    source = tmp_path / "sourcedir"
    dest = tmp_path / "destdir"
    source.mkdir()
    (source / "file.txt").write_text("content")

    result = await _move_file_impl(str(source), str(dest))

    assert result["success"] is True
    assert not source.exists()
    assert dest.exists()
    assert (dest / "file.txt").exists()


# ============================================================================
# delete_file tests
# ============================================================================


@pytest.mark.asyncio
async def test_delete_file_simple(tmp_path):
    """Test deleting a file"""
    file_path = tmp_path / "test.txt"
    file_path.write_text("content")

    result = await _delete_file_impl(str(file_path))

    assert result["success"] is True
    assert not file_path.exists()


@pytest.mark.asyncio
async def test_delete_file_not_found(tmp_path):
    """Test deleting a non-existent file"""
    file_path = tmp_path / "nonexistent.txt"

    result = await _delete_file_impl(str(file_path))

    assert "error" in result
    assert "not found" in result["error"].lower()


@pytest.mark.asyncio
async def test_delete_file_is_directory(tmp_path):
    """Test deleting a directory with delete_file (should fail)"""
    dir_path = tmp_path / "testdir"
    dir_path.mkdir()

    result = await _delete_file_impl(str(dir_path))

    assert "error" in result
    assert "not a file" in result["error"].lower()


# ============================================================================
# delete_directory tests
# ============================================================================


@pytest.mark.asyncio
async def test_delete_directory_empty(tmp_path):
    """Test deleting an empty directory"""
    dir_path = tmp_path / "emptydir"
    dir_path.mkdir()

    result = await _delete_directory_impl(str(dir_path), recursive=False)

    assert result["success"] is True
    assert not dir_path.exists()


@pytest.mark.asyncio
async def test_delete_directory_not_empty_without_recursive(tmp_path):
    """Test deleting a non-empty directory without recursive flag"""
    dir_path = tmp_path / "nonempty"
    dir_path.mkdir()
    (dir_path / "file.txt").write_text("content")

    result = await _delete_directory_impl(str(dir_path), recursive=False)

    assert "error" in result
    assert "not empty" in result["error"].lower()
    assert dir_path.exists()


@pytest.mark.asyncio
async def test_delete_directory_recursive(tmp_path):
    """Test deleting a non-empty directory with recursive flag"""
    dir_path = tmp_path / "nonempty"
    dir_path.mkdir()
    (dir_path / "file.txt").write_text("content")
    subdir = dir_path / "subdir"
    subdir.mkdir()
    (subdir / "nested.txt").write_text("nested content")

    result = await _delete_directory_impl(str(dir_path), recursive=True)

    assert result["success"] is True
    assert not dir_path.exists()


@pytest.mark.asyncio
async def test_delete_directory_not_found(tmp_path):
    """Test deleting a non-existent directory"""
    dir_path = tmp_path / "nonexistent"

    result = await _delete_directory_impl(str(dir_path), recursive=False)

    assert "error" in result
    assert "not found" in result["error"].lower()


@pytest.mark.asyncio
async def test_delete_directory_is_file(tmp_path):
    """Test deleting a file with delete_directory (should fail)"""
    file_path = tmp_path / "test.txt"
    file_path.write_text("content")

    result = await _delete_directory_impl(str(file_path), recursive=False)

    assert "error" in result
    assert "not a directory" in result["error"].lower()


# ============================================================================
# get_file_info tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_file_info_file(tmp_path):
    """Test getting info for a file"""
    file_path = tmp_path / "test.txt"
    content = "Hello World"
    file_path.write_text(content)

    result = await _get_file_info_impl(str(file_path))

    assert result["success"] is True
    assert result["name"] == "test.txt"
    assert result["type"] == "file"
    assert result["size"] == len(content)
    assert result["extension"] == ".txt"
    assert "modified" in result
    assert "created" in result
    assert "permissions" in result


@pytest.mark.asyncio
async def test_get_file_info_directory(tmp_path):
    """Test getting info for a directory"""
    dir_path = tmp_path / "testdir"
    dir_path.mkdir()

    result = await _get_file_info_impl(str(dir_path))

    assert result["success"] is True
    assert result["name"] == "testdir"
    assert result["type"] == "directory"
    assert "size" in result
    assert "modified" in result
    assert "created" in result
    assert "permissions" in result
    assert "extension" not in result  # Directories don't have extensions


@pytest.mark.asyncio
async def test_get_file_info_not_found(tmp_path):
    """Test getting info for a non-existent path"""
    file_path = tmp_path / "nonexistent.txt"

    result = await _get_file_info_impl(str(file_path))

    assert "error" in result
    assert "not found" in result["error"].lower()


@pytest.mark.asyncio
async def test_get_file_info_no_extension(tmp_path):
    """Test getting info for a file without extension"""
    file_path = tmp_path / "README"
    file_path.write_text("content")

    result = await _get_file_info_impl(str(file_path))

    assert result["success"] is True
    assert result["extension"] == ""


# ============================================================================
# Integration tests
# ============================================================================


@pytest.mark.asyncio
async def test_full_workflow(tmp_path):
    """Test a complete workflow: create, read, move, delete"""
    # Create directory
    dir_path = tmp_path / "mydir"
    result = await _create_directory_impl(str(dir_path))
    assert result["success"] is True

    # Write file
    file_path = dir_path / "test.txt"
    content = "Test content"
    result = await _write_file_impl(str(file_path), content)
    assert result["success"] is True

    # Read file
    result = await _read_file_impl(str(file_path))
    assert result["success"] is True
    assert result["content"] == content

    # List directory
    result = await _list_directory_impl(str(dir_path))
    assert result["success"] is True
    assert result["count"] == 1

    # Get file info
    result = await _get_file_info_impl(str(file_path))
    assert result["success"] is True
    assert result["type"] == "file"

    # Move file
    new_path = dir_path / "renamed.txt"
    result = await _move_file_impl(str(file_path), str(new_path))
    assert result["success"] is True

    # Delete file
    result = await _delete_file_impl(str(new_path))
    assert result["success"] is True

    # Delete directory
    result = await _delete_directory_impl(str(dir_path), recursive=False)
    assert result["success"] is True
    assert not dir_path.exists()
