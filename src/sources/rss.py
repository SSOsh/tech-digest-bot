"""일반 RSS 소스"""
import time
from datetime import datetime, timedelta, timezone

import feedparser
import requests

from src.sources.base import Article, Source
from src.filter import matches_keywords

REQUEST_TIMEOUT = 15
REQUEST_DELAY = 0.5
MAX_RETRIES = 3


class RSSSource(Source):
    """일반 RSS 피드 소스"""

    def __init__(self, source_id: str, name: str, feed_url: str):
        self._id = source_id
        self._name = name
        self._url = feed_url

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def url(self) -> str:
        return self._url

    def _parse_feed(self) -> list:
        """RSS 피드 파싱 (재시도 포함)"""
        for attempt in range(MAX_RETRIES):
            try:
                # User-Agent 설정으로 차단 방지
                feed = feedparser.parse(
                    self._url,
                    request_headers={"User-Agent": "TechDigestBot/1.0"}
                )
                if feed.bozo and not feed.entries:
                    raise Exception(f"피드 파싱 실패: {feed.bozo_exception}")
                return feed.entries
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)  # 지수 백오프
                    continue
                raise e
        return []

    def fetch_articles(
        self, hours: int = 24, top_n: int | None = None, limit: int | None = None, keywords: list[str] | None = None
    ) -> list[Article]:
        """RSS 피드에서 기사 수집

        Args:
            hours: 수집할 시간 범위
            top_n: 사용하지 않음 (RSS는 점수 지원 안 함)
            limit: 최대 기사 수 제한 (None이면 전체)
            keywords: 키워드 필터 (제목 매칭)
        """
        try:
            entries = self._parse_feed()
        except Exception as e:
            print(f"[ERROR] {self._name} 피드 파싱 실패: {e}")
            return []

        articles = []
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        for entry in entries:
            # limit이 설정된 경우 조기 종료
            if limit is not None and len(articles) >= limit:
                break

            try:
                # 발행일 파싱 (타임존 고려)
                published = entry.get("published_parsed") or entry.get("updated_parsed")
                if published:
                    # struct_time을 datetime으로 변환 (UTC로 간주)
                    pub_dt = datetime(*published[:6], tzinfo=timezone.utc)

                    # 일부 RSS는 로컬 타임존 정보를 제공하지 않으므로,
                    # published_parsed는 항상 UTC로 처리됨 (feedparser 스펙)
                    if pub_dt < cutoff:
                        continue
                else:
                    # 발행일이 없으면 현재 시간 사용 (필터링되지 않도록)
                    pub_dt = datetime.now(timezone.utc)

                title = entry.get("title", "").strip()
                url = entry.get("link", "")

                if not title or not url:
                    continue

                # 키워드 필터링
                temp_article = Article(
                    title=title,
                    url=url,
                    source_id=self._id,
                    source_name=self._name,
                    points=None,
                    published_at=pub_dt,
                )

                if keywords and not matches_keywords(temp_article, keywords):
                    continue

                articles.append(temp_article)

            except Exception as e:
                print(f"[WARN] {self._name} 기사 파싱 실패: {e}")
                continue

        time.sleep(REQUEST_DELAY)
        return articles
