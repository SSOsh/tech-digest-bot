"""키워드/점수 필터링 모듈"""
import re

from src.sources.base import Article


def matches_keywords(article: Article, keywords: list[str]) -> bool:
    """기사 제목이 키워드와 매칭되는지 확인 (대소문자 무시)"""
    if not keywords:
        return True  # 키워드가 없으면 모든 기사 통과

    title_lower = article.title.lower()

    for keyword in keywords:
        pattern = rf"\b{re.escape(keyword.lower())}\b"
        if re.search(pattern, title_lower):
            return True

    return False


def filter_articles(
    articles: list[Article],
    keywords: list[str],
    min_points: int = 0,
) -> list[Article]:
    """점수와 키워드 기준으로 기사 필터링"""
    filtered = []

    for article in articles:
        # 최소 점수 체크 (GeekNews처럼 점수 지원하는 소스만)
        if article.points is not None and article.points < min_points:
            continue

        # 키워드 매칭 체크
        if not matches_keywords(article, keywords):
            continue

        filtered.append(article)

    # 점수 있는 것 우선, 그 다음 시간순
    def sort_key(a: Article):
        return (
            -(a.points or 0),  # 점수 높은 순
            -(a.published_at.timestamp() if a.published_at else 0),  # 최신순
        )

    filtered.sort(key=sort_key)

    return filtered
