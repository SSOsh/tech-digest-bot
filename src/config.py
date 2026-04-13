"""설정 로딩 모듈"""
import os
from pathlib import Path

import yaml
from pydantic import BaseModel

from src.sources.registry import list_source_ids


class UserConfig(BaseModel):
    """사용자 설정"""
    id: str
    sources: list[str] = []  # 구독할 소스 ID 목록 (비어있으면 전체)
    keywords: list[str] = []
    min_points: int = 0  # GeekNews에만 적용
    hours: int = 72  # 수집 기간 (기본 3일)

    # 알림 설정
    slack: bool = True
    email: str | None = None


class Config(BaseModel):
    """전체 설정"""
    users: list[UserConfig]


def load_config(path: Path | None = None) -> Config:
    """users_config.yaml 로드"""
    if path is None:
        path = Path(__file__).parent.parent / "users_config.yaml"

    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    config = Config(**data)

    # 소스 ID 유효성 검사
    valid_sources = set(list_source_ids())
    for user in config.users:
        if user.sources:
            invalid = set(user.sources) - valid_sources
            if invalid:
                print(f"[WARN] {user.id}: 알 수 없는 소스 - {invalid}")
                user.sources = [s for s in user.sources if s in valid_sources]

    return config


def get_slack_webhook(user_id: str) -> str | None:
    """환경변수에서 Slack Webhook URL 가져오기"""
    env_key = f"SLACK_WEBHOOK_{user_id.upper()}"
    return os.getenv(env_key)
