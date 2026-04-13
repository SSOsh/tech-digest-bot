"""소스 레지스트리"""
from src.sources.base import Source
from src.sources.geeknews import GeekNewsSource
from src.sources.rss import RSSSource

# 국내 RSS 소스 목록
_SOURCES: dict[str, Source] = {
    # 커뮤니티
    "geeknews": GeekNewsSource(),
    "yozm": RSSSource(
        source_id="yozm",
        name="요즘IT",
        feed_url="https://yozm.wishket.com/magazine/feed/",
    ),
    "velog": RSSSource(
        source_id="velog",
        name="velog",
        feed_url="https://v2.velog.io/rss",
    ),
    # 기업 테크블로그
    "kakao": RSSSource(
        source_id="kakao",
        name="카카오 테크",
        feed_url="https://tech.kakao.com/feed/",
    ),
    "toss": RSSSource(
        source_id="toss",
        name="토스 테크",
        feed_url="https://toss.tech/rss.xml",
    ),
    "daangn": RSSSource(
        source_id="daangn",
        name="당근 테크",
        feed_url="https://medium.com/feed/daangn",
    ),
    "line": RSSSource(
        source_id="line",
        name="라인 테크",
        feed_url="https://techblog.lycorp.co.jp/ko/feed/index.xml",
    ),
    "nhn": RSSSource(
        source_id="nhn",
        name="NHN 밋업",
        feed_url="https://meetup.nhncloud.com/rss",
    ),
    "hyperconnect": RSSSource(
        source_id="hyperconnect",
        name="하이퍼커넥트",
        feed_url="https://hyperconnect.github.io/feed.xml",
    ),
}


def get_source(source_id: str) -> Source | None:
    """소스 ID로 소스 가져오기"""
    return _SOURCES.get(source_id)


def get_all_sources() -> dict[str, Source]:
    """모든 소스 가져오기"""
    return _SOURCES.copy()


def list_source_ids() -> list[str]:
    """사용 가능한 소스 ID 목록"""
    return list(_SOURCES.keys())
