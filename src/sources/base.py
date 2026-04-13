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
    def fetch_articles(self, hours: int = 24) -> list[Article]:
        """기사 수집"""
        ...
