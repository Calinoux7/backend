# tests/conftest.py
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add the backend folder to Python's import path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import article
import main
from rate_limit import reset_rate_limits


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Provides a TestClient with articles/images/trash redirected to a temp folder."""
    articles_dir = tmp_path / "articles"
    images_dir = tmp_path / "images"
    trash_dir = tmp_path / "trash"
    articles_dir.mkdir()
    images_dir.mkdir()
    trash_dir.mkdir()

    monkeypatch.setattr(article, "ARTICLES_DIR", articles_dir)
    monkeypatch.setattr(main, "ARTICLES_DIR", articles_dir)
    monkeypatch.setattr(main, "IMAGES_DIR", images_dir)
    monkeypatch.setattr(main, "TRASH_DIR", trash_dir)

    # Reset in-memory state between tests, so tests don't affect each other.
    main.comments.clear()
    monkeypatch.setattr(main, "_next_comment_id", 1)
    reset_rate_limits()

    return TestClient(main.app)