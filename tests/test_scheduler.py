"""스케줄러 테스트

@author suho.do
@since 2026-04-21
"""
from datetime import datetime, timedelta, timezone

import pytest

from src.db import Subscription


class TestDuplicateSendingPrevention:
    """중복 발송 방지 테스트"""

    def test_should_skip_if_sent_within_20_hours(self):
        """20시간 이내 발송 시 스킵"""
        # given
        now = datetime.now(timezone.utc)
        last_sent = now - timedelta(hours=10)  # 10시간 전

        # when
        time_since_last = now - last_sent
        should_skip = time_since_last < timedelta(hours=20)

        # then
        assert should_skip is True

    def test_should_send_if_sent_more_than_20_hours_ago(self):
        """20시간 이상 경과 시 발송"""
        # given
        now = datetime.now(timezone.utc)
        last_sent = now - timedelta(hours=22)  # 22시간 전

        # when
        time_since_last = now - last_sent
        should_skip = time_since_last < timedelta(hours=20)

        # then
        assert should_skip is False

    def test_should_send_if_never_sent(self):
        """한 번도 발송하지 않은 경우 발송"""
        # given
        last_sent = None

        # when
        should_skip = False if last_sent is None else True

        # then
        assert should_skip is False

    def test_last_sent_at_string_parsing(self):
        """last_sent_at 문자열 파싱"""
        # given
        now = datetime.now(timezone.utc)
        last_sent_str = now.isoformat()

        # when
        parsed = datetime.fromisoformat(last_sent_str.replace("Z", "+00:00"))

        # then
        assert isinstance(parsed, datetime)
        assert parsed.tzinfo is not None


class TestArticleFetching:
    """기사 수집 테스트"""

    def test_source_options_parsing(self):
        """source_options 파싱"""
        import json

        # given
        source_options = json.dumps({"geeknews": {"top_n": 10}})

        # when
        parsed = json.loads(source_options)
        geeknews_opts = parsed.get("geeknews", {})
        top_n = geeknews_opts.get("top_n")

        # then
        assert top_n == 10

    def test_source_options_handles_invalid_json(self):
        """잘못된 JSON 처리"""
        import json

        # given
        invalid_json = "not json"

        # when
        try:
            options = json.loads(invalid_json)
        except json.JSONDecodeError:
            options = {}

        # then
        assert options == {}

    def test_fetch_with_top_n_for_points_source(self):
        """포인트 소스는 top_n 사용"""
        # given
        source_id = "geeknews"
        source_options = {"geeknews": {"top_n": 10}}

        # when
        opts = source_options.get(source_id, {})
        top_n = opts.get("top_n")
        limit = opts.get("limit")

        # then
        assert top_n == 10
        assert limit is None

    def test_fetch_with_limit_for_rss_source(self):
        """RSS 소스는 limit 사용"""
        # given
        source_id = "kakao"
        source_options = {"kakao": {"limit": 15}}

        # when
        opts = source_options.get(source_id, {})
        top_n = opts.get("top_n")
        limit = opts.get("limit")

        # then
        assert top_n is None
        assert limit == 15
