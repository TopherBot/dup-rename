import os
import shutil
import tempfile
from pathlib import Path

from dup_rename import sha256_file, group_by_hash, auto_rename

def create_file(path: Path, content: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)

def test_sha256_consistency(tmp_path: Path):
    file_a = tmp_path / "a.txt"
    create_file(file_a, b"hello world")
    h1 = sha256_file(file_a)
    h2 = sha256_file(file_a)
    assert h1 == h2

def test_duplicate_detection_and_rename(tmp_path: Path):
    # Create duplicate set
    dup1 = tmp_path / "dir1" / "dup.txt"
    dup2 = tmp_path / "dir2" / "duplicate.txt"
    dup3 = tmp_path / "dup.txt"  # same root folder
    for p in [dup1, dup2, dup3]:
        create_file(p, b"same content")

    # One unique file
    uniq = tmp_path / "unique.txt"
    create_file(uniq, b"different content")

    dup_map = group_by_hash(tmp_path)
    assert len(dup_map) == 1  # only the duplicate hash group
    assert sum(len(v) for v in dup_map.values()) == 3

    renamed = auto_rename(dup_map)
    # Should rename 2 files (keep first original)
    assert len(renamed) == 2
    # Verify new names exist and old ones are gone
    for old, new in renamed:
        assert not old.exists()
        assert new.exists()
        assert new.stem.startswith(old.stem)

    # Ensure unique file untouched
    assert uniq.exists()

# Run tests when executed directly (useful for local debugging)
if __name__ == "__main__":
    import pytest, sys
    sys.exit(pytest.main([__file__]))
