"""pytest fixtures

@author suho.do
@since 2026-04-21
"""
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_db_path():
    """임시 DB 경로 생성"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "test.db"


@pytest.fixture
def mock_articles():
    """테스트용 기사 목록 생성"""
    from datetime import datetime, timezone
    from src.sources.base import Article

    return [
        Article(
            title="Test Article 1",
            url="https://example.com/1",
            source_id="test",
            source_name="Test Source",
            points=100,
            published_at=datetime.now(timezone.utc),
        ),
        Article(
            title="Test Article 2",
            url="https://example.com/2",
            source_id="test",
            source_name="Test Source",
            points=50,
            published_at=datetime.now(timezone.utc),
        ),
    ]
