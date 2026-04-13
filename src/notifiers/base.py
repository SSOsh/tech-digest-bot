"""알림 기본 인터페이스"""
from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.sources.base import Article


@dataclass
class NotifyResult:
    """알림 전송 결과"""
    success: bool
    channel: str  # "slack", "email"
    message: str = ""


class Notifier(ABC):
    """알림 인터페이스"""

    @property
    @abstractmethod
    def channel(self) -> str:
        """알림 채널 이름"""
        ...

    @abstractmethod
    def send(self, articles: list[Article], user_id: str) -> NotifyResult:
        """알림 전송"""
        ...
