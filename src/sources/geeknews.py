"""GeekNews 소스 (점수 스크래핑 지원)"""
import re
import time
from datetime import datetime, timedelta, timezone

import feedparser
import requests
from bs4 import BeautifulSoup

from src.sources.base import Article, Source
from src.filter import matches_keywords

RSS_URL = "https://news.hada.io/rss"
REQUEST_TIMEOUT = 15
SCRAPE_DELAY = 1.0
MAX_RETRIES = 3


class GeekNewsSource(Source):
    """GeekNews 소스 (점수 스크래핑 포함)"""

    @property
    def id(self) -> str:
        return "geeknews"

    @property
    def name(self) -> str:
        return "GeekNews"

    @property
    def url(self) -> str:
        return RSS_URL

    @property
    def supports_points(self) -> bool:
        return True

    def _scrape_points(self, article_url: str) -> int | None:
        """기사 페이지에서 추천 점수 스크래핑"""
        for attempt in range(MAX_RETRIES):
            try:
                resp = requests.get(
                    article_url,
                    timeout=REQUEST_TIMEOUT,
                    headers={"User-Agent": "TechDigestBot/1.0"}
                )
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")

                # GeekNews 포인트 형식: 다양한 셀렉터 시도
                selectors = [".topictitle .u", ".topic_status", ".points"]
                for selector in selectors:
                    elem = soup.select_one(selector)
                    if elem:
                        text = elem.get_text(strip=True)
                        match = re.search(r"(\d+)", text)
                        if match:
                            return int(match.group(1))
                return None  # 포인트를 찾지 못한 경우
            except Exception:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(1)
                    continue
                return None  # 스크래핑 실패 시 None 반환
        return None

    def fetch_articles(
        self, hours: int = 24, top_n: int | None = None, limit: int | None = None, keywords: list[str] | None = None
    ) -> list[Article]:
        """기사 수집 (점수 포함, 키워드 필터링 우선 적용)

        Args:
            hours: 수집할 시간 범위
            top_n: 점수 기준 상위 N개 선택 (None이면 전체)
            limit: 사용하지 않음 (top_n 우선)
            keywords: 키워드 필터 (제목 매칭, 스크래핑 전에 먼저 필터링)
        """
        try:
            feed = feedparser.parse(
                RSS_URL,
                request_headers={"User-Agent": "TechDigestBot/1.0"}
            )
            if feed.bozo and not feed.entries:
                print(f"[ERROR] GeekNews 피드 파싱 실패")
                return []
        except Exception as e:
            print(f"[ERROR] GeekNews 피드 요청 실패: {e}")
            return []

        # 1단계: 시간 필터링 및 키워드 필터링 (포인트 스크래핑 전)
        candidates = []
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        for entry in feed.entries:
            try:
                published = entry.get("published_parsed")
                if published:
                    pub_dt = datetime(*published[:6], tzinfo=timezone.utc)
                    if pub_dt < cutoff:
                        continue
                else:
                    pub_dt = datetime.now(timezone.utc)

                title = entry.get("title", "").strip()
                article_url = entry.get("link", "")

                if not title or not article_url:
                    continue

                # 임시 Article 객체 생성 (키워드 필터용)
                temp_article = Article(
                    title=title,
                    url=article_url,
                    source_id=self.id,
                    source_name=self.name,
                    points=None,
                    published_at=pub_dt,
                )

                # 키워드 필터링 (포인트 스크래핑 전에 수행)
                if keywords and not matches_keywords(temp_article, keywords):
                    continue

                candidates.append((title, article_url, pub_dt))

            except Exception as e:
                print(f"[WARN] GeekNews 기사 파싱 실패: {e}")
                continue

        print(f"[INFO] GeekNews: 키워드 필터 후 {len(candidates)}개 기사 (포인트 스크래핑 시작)")

        # 2단계: 필터링된 기사에 대해서만 포인트 스크래핑
        articles = []
        for title, article_url, pub_dt in candidates:
            try:
                points = self._scrape_points(article_url)
                time.sleep(SCRAPE_DELAY)

                articles.append(
                    Article(
                        title=title,
                        url=article_url,
                        source_id=self.id,
                        source_name=self.name,
                        points=points,
                        published_at=pub_dt,
                    )
                )
            except Exception as e:
                print(f"[WARN] GeekNews 포인트 스크래핑 실패: {e}")
                continue

        # 점수 기준 내림차순 정렬 (None은 0으로 취급)
        articles.sort(key=lambda a: a.points if a.points is not None else 0, reverse=True)

        # top_n이 지정된 경우 상위 N개만 반환
        if top_n is not None and top_n > 0:
            articles = articles[:top_n]

        return articles
