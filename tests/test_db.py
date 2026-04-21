"""DB 관련 테스트

@author suho.do
@since 2026-04-21
"""
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.db import (
    DB_PATH,
    Subscription,
    add_subscription,
    delete_subscription,
    get_subscription_by_email,
    get_subscription_by_token,
    init_db,
    update_last_sent_at,
)


@pytest.fixture
def temp_db(monkeypatch):
    """임시 DB 생성"""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_db_path = Path(tmpdir) / "test.db"
        monkeypatch.setattr("src.db.DB_PATH", temp_db_path)
        init_db()
        yield temp_db_path


class TestSubscription:
    """구독 관련 테스트"""

    def test_add_subscription_generates_token(self, temp_db):
        """구독 추가 시 토큰 자동 생성"""
        # given
        sub = Subscription(
            id=None,
            email="test@example.com",
            slack_webhook=None,
            keywords="python,ai",
            sources="geeknews",
            min_points=10,
        )

        # when
        sub_id = add_subscription(sub)

        # then
        saved_sub = get_subscription_by_email("test@example.com")
        assert saved_sub is not None
        assert saved_sub.unsubscribe_token is not None
        assert len(saved_sub.unsubscribe_token) > 0

    def test_delete_subscription_requires_token(self, temp_db):
        """구독 삭제 시 토큰 검증 필수"""
        # given
        sub = Subscription(
            id=None,
            email="test@example.com",
            slack_webhook=None,
            keywords="",
            sources="",
            min_points=0,
        )
        sub_id = add_subscription(sub)
        saved_sub = get_subscription_by_email("test@example.com")

        # when - 잘못된 토큰으로 삭제 시도
        result1 = delete_subscription(sub_id, "invalid_token")

        # then
        assert result1 is False
        assert get_subscription_by_email("test@example.com") is not None

        # when - 올바른 토큰으로 삭제
        result2 = delete_subscription(sub_id, saved_sub.unsubscribe_token)

        # then
        assert result2 is True
        assert get_subscription_by_email("test@example.com") is None

    def test_get_subscription_by_token(self, temp_db):
        """토큰으로 구독 조회"""
        # given
        sub = Subscription(
            id=None,
            email="test@example.com",
            slack_webhook=None,
            keywords="",
            sources="",
            min_points=0,
        )
        add_subscription(sub)
        saved_sub = get_subscription_by_email("test@example.com")

        # when
        result = get_subscription_by_token(saved_sub.unsubscribe_token)

        # then
        assert result is not None
        assert result.email == "test@example.com"
        assert result.id == saved_sub.id

    def test_update_last_sent_at(self, temp_db):
        """마지막 발송 시간 업데이트"""
        # given
        sub = Subscription(
            id=None,
            email="test@example.com",
            slack_webhook=None,
            keywords="",
            sources="",
            min_points=0,
        )
        sub_id = add_subscription(sub)

        # when
        result = update_last_sent_at(sub_id)

        # then
        assert result is True
        saved_sub = get_subscription_by_email("test@example.com")
        assert saved_sub.last_sent_at is not None

    def test_duplicate_email_check(self, temp_db):
        """중복 이메일 체크"""
        # given
        sub1 = Subscription(
            id=None,
            email="test@example.com",
            slack_webhook=None,
            keywords="",
            sources="",
            min_points=0,
        )
        add_subscription(sub1)

        # when
        existing = get_subscription_by_email("test@example.com")

        # then
        assert existing is not None
        assert existing.email == "test@example.com"
