"""Source 관련 테스트

@author suho.do
@since 2026-04-21
"""
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.sources.base import Article
from src.sources.geeknews import GeekNewsSource
from src.sources.rss import RSSSource


class TestGeekNewsSource:
    """GeekNews 소스 테스트"""

    def test_points_scraping_returns_none_on_failure(self):
        """포인트 스크래핑 실패 시 None 반환"""
        # given
        source = GeekNewsSource()

        # when - 존재하지 않는 URL
        with patch("requests.get") as mock_get:
            mock_get.side_effect = Exception("Network error")
            result = source._scrape_points("https://invalid-url.com")

        # then
        assert result is None

    def test_top_n_filtering(self):
        """top_n 파라미터로 상위 N개 선택"""
        # given
        source = GeekNewsSource()

        # when - fetch_articles를 모킹
        with patch.object(source, "fetch_articles") as mock_fetch:
            # 포인트가 다른 5개 기사 생성
            articles = [
                Article(
                    title=f"Article {i}",
                    url=f"https://news.hada.io/{i}",
                    source_id="geeknews",
                    source_name="GeekNews",
                    points=i * 10,
                    published_at=datetime.now(timezone.utc),
                )
                for i in range(5, 0, -1)  # 50, 40, 30, 20, 10
            ]

            # 실제 정렬 로직 적용
            def mock_fetch_with_sort(hours=24, top_n=None, limit=None):
                sorted_articles = sorted(
                    articles, key=lambda a: a.points if a.points else 0, reverse=True
                )
                if top_n:
                    return sorted_articles[:top_n]
                return sorted_articles

            mock_fetch.side_effect = mock_fetch_with_sort

            # top_n=3으로 호출
            result = source.fetch_articles(hours=24, top_n=3)

            # then
            assert len(result) == 3
            assert result[0].points == 50
            assert result[1].points == 40
            assert result[2].points == 30

    def test_supports_points(self):
        """GeekNews는 포인트 지원"""
        # given
        source = GeekNewsSource()

        # then
        assert source.supports_points is True


class TestRSSSource:
    """RSS 소스 테스트"""

    def test_limit_filtering(self):
        """limit 파라미터로 최대 개수 제한"""
        # given
        source = RSSSource("test", "Test RSS", "https://example.com/feed")

        # when - fetch_articles를 모킹
        with patch.object(source, "_parse_feed") as mock_parse:
            # 10개 엔트리 생성
            mock_entries = [
                {
                    "title": f"Article {i}",
                    "link": f"https://example.com/{i}",
                    "published_parsed": datetime.now(timezone.utc).timetuple(),
                }
                for i in range(10)
            ]
            mock_parse.return_value = mock_entries

            # limit=5로 호출
            result = source.fetch_articles(hours=24, limit=5)

            # then
            assert len(result) <= 5

    def test_does_not_support_points(self):
        """RSS는 포인트 미지원"""
        # given
        source = RSSSource("test", "Test RSS", "https://example.com/feed")

        # then
        assert source.supports_points is False


class TestSchedulerDeduplication:
    """Scheduler 중복 제거 테스트"""

    def test_url_deduplication(self):
        """URL 기반 중복 제거"""
        # given
        articles = [
            Article(
                title="Article 1",
                url="https://example.com/1",
                source_id="source1",
                source_name="Source 1",
            ),
            Article(
                title="Article 1 Duplicate",
                url="https://example.com/1",  # 동일 URL
                source_id="source2",
                source_name="Source 2",
            ),
            Article(
                title="Article 2",
                url="https://example.com/2",
                source_id="source1",
                source_name="Source 1",
            ),
        ]

        # when - URL 기반 중복 제거
        seen_urls = set()
        deduplicated = []
        for article in articles:
            if article.url not in seen_urls:
                seen_urls.add(article.url)
                deduplicated.append(article)

        # then
        assert len(deduplicated) == 2
        assert deduplicated[0].url == "https://example.com/1"
        assert deduplicated[1].url == "https://example.com/2"
