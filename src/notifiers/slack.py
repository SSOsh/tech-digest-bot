"""Slack 알림"""
import requests

from src.notifiers.base import Notifier, NotifyResult
from src.sources.base import Article

REQUEST_TIMEOUT = 10


class SlackNotifier(Notifier):
    """Slack Webhook 알림"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    @property
    def channel(self) -> str:
        return "slack"

    def _format_message(self, articles: list[Article]) -> dict:
        """Slack Block Kit 형식으로 메시지 포맷팅"""
        if not articles:
            return {
                "text": "오늘은 관심 키워드와 매칭되는 뉴스가 없습니다.",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": ":mailbox_with_no_mail: 오늘은 관심 키워드와 매칭되는 뉴스가 없습니다.",
                        },
                    }
                ],
            }

        # 소스별로 그룹핑
        by_source: dict[str, list[Article]] = {}
        for article in articles:
            if article.source_name not in by_source:
                by_source[article.source_name] = []
            by_source[article.source_name].append(article)

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f":newspaper: 데일리 테크 다이제스트 ({len(articles)}건)",
                },
            },
            {"type": "divider"},
        ]

        for source_name, source_articles in by_source.items():
            blocks.append(
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"*{source_name}* ({len(source_articles)}건)",
                        }
                    ],
                }
            )

            for article in source_articles:
                points_text = f" | :thumbsup: {article.points}P" if article.points else ""
                blocks.append(
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"<{article.url}|{article.title}>{points_text}",
                        },
                    }
                )

            blocks.append({"type": "divider"})

        blocks.append(
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "Powered by Tech Digest Bot",
                    }
                ],
            }
        )

        return {"blocks": blocks}

    def send(self, articles: list[Article], user_id: str) -> NotifyResult:
        """Slack으로 메시지 전송"""
        try:
            payload = self._format_message(articles)
            resp = requests.post(self.webhook_url, json=payload, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return NotifyResult(success=True, channel=self.channel)
        except Exception as e:
            return NotifyResult(success=False, channel=self.channel, message=str(e))
