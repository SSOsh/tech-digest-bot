# Deprecated: src/notifiers/ 모듈로 대체됨
# 하위 호환성을 위해 유지

from src.notifiers import SlackNotifier

__all__ = ["send_slack"]


def send_slack(webhook_url: str, articles: list, user_id: str) -> bool:
    """[Deprecated] Slack으로 메시지 전송"""
    notifier = SlackNotifier(webhook_url)
    result = notifier.send(articles, user_id)
    return result.success
