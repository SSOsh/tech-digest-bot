"""GeekNews 소스 (점수 스크래핑 지원)"""
import re
import time
from datetime import datetime, timedelta, timezone

import feedparser
import requests
from bs4 import BeautifulSoup

from src.sources.base import Article, Source

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

    def _scrape_points(self, article_url: str) -> int:
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
                return 0
            except Exception:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(1)
                    continue
                return 0
        return 0

    def fetch_articles(self, hours: int = 24) -> list[Article]:
        """기사 수집 (점수 포함)"""
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

        articles = []
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

                # 점수 스크래핑
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
                print(f"[WARN] GeekNews 기사 파싱 실패: {e}")
                continue

        return articles
