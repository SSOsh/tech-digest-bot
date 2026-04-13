# Deprecated: src/sources/ 모듈로 대체됨
# 하위 호환성을 위해 유지

from src.sources import Article, get_all_sources

__all__ = ["Article", "fetch_articles"]


def fetch_articles(hours: int = 24) -> list[Article]:
    """[Deprecated] 모든 소스에서 기사 수집"""
    articles = []
    for source in get_all_sources().values():
        try:
            articles.extend(source.fetch_articles(hours=hours))
        except Exception:
            pass
    return articles
