"""소스 기본 인터페이스"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Article:
    """기사 데이터"""
    title: str
    url: str
    source_id: str
    source_name: str
    points: int | None = None  # 점수 (지원하는 소스만)
    published_at: datetime | None = None


class Source(ABC):
    """뉴스 소스 인터페이스"""

    @property
    @abstractmethod
    def id(self) -> str:
        """소스 고유 ID"""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """소스 표시 이름"""
        ...

    @property
    @abstractmethod
    def url(self) -> str:
        """RSS 피드 URL"""
        ...

    @property
    def supports_points(self) -> bool:
        """점수 지원 여부"""
        return False

    @abstractmethod
    def fetch_articles(
        self, hours: int = 24, top_n: int | None = None, limit: int | None = None, keywords: list[str] | None = None
    ) -> list[Article]:
        """기사 수집

        Args:
            hours: 수집할 시간 범위
            top_n: 점수 기준 상위 N개 선택 (supports_points=True인 소스만)
            limit: 최대 기사 수 제한 (RSS 소스 등)
            keywords: 키워드 필터 (제목 매칭, 대소문자 무시)
        """
        ...
