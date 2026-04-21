"""이메일 알림"""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.notifiers.base import Notifier, NotifyResult
from src.sources.base import Article


class EmailNotifier(Notifier):
    """SMTP 이메일 알림"""

    def __init__(self, to_email: str):
        self.to_email = to_email
        # 환경변수에서 SMTP 설정 로드
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("SMTP_FROM", self.smtp_user)

    @property
    def channel(self) -> str:
        return "email"

    def _format_html(self, articles: list[Article]) -> str:
        """HTML 이메일 본문 생성"""
        if not articles:
            return """
            <html>
            <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                <p>오늘은 관심 키워드와 매칭되는 뉴스가 없습니다.</p>
            </body>
            </html>
            """

        # 소스별로 그룹핑
        by_source: dict[str, list[Article]] = {}
        for article in articles:
            if article.source_name not in by_source:
                by_source[article.source_name] = []
            by_source[article.source_name].append(article)

        sections = []
        for source_name, source_articles in by_source.items():
            items = []
            for article in source_articles:
                points = f" <span style='color: #666;'>({article.points}P)</span>" if article.points else ""
                items.append(
                    f'<li style="margin-bottom: 8px;">'
                    f'<a href="{article.url}" style="color: #0066cc; text-decoration: none;">{article.title}</a>'
                    f'{points}</li>'
                )

            sections.append(f"""
                <div style="margin-bottom: 24px;">
                    <h3 style="color: #333; border-bottom: 1px solid #eee; padding-bottom: 8px;">
                        {source_name} ({len(source_articles)}건)
                    </h3>
                    <ul style="padding-left: 20px;">
                        {''.join(items)}
                    </ul>
                </div>
            """)

        return f"""
        <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h1 style="color: #333;">📰 데일리 테크 다이제스트</h1>
            <p style="color: #666;">총 {len(articles)}건의 뉴스가 있습니다.</p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            {''.join(sections)}
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="color: #999; font-size: 12px;">Powered by Tech Digest Bot</p>
        </body>
        </html>
        """

    def _format_plain(self, articles: list[Article]) -> str:
        """Plain text 이메일 본문 생성"""
        if not articles:
            return "오늘은 관심 키워드와 매칭되는 뉴스가 없습니다."

        lines = [f"📰 데일리 테크 다이제스트 ({len(articles)}건)", "=" * 40, ""]

        by_source: dict[str, list[Article]] = {}
        for article in articles:
            if article.source_name not in by_source:
                by_source[article.source_name] = []
            by_source[article.source_name].append(article)

        for source_name, source_articles in by_source.items():
            lines.append(f"\n## {source_name} ({len(source_articles)}건)")
            lines.append("-" * 30)
            for article in source_articles:
                points = f" ({article.points}P)" if article.points else ""
                lines.append(f"• {article.title}{points}")
                lines.append(f"  {article.url}")
            lines.append("")

        lines.append("=" * 40)
        lines.append("Powered by Tech Digest Bot")

        return "\n".join(lines)

    def send(self, articles: list[Article], user_id: str) -> NotifyResult:
        """이메일 전송"""
        if not self.smtp_user or not self.smtp_password:
            return NotifyResult(
                success=False,
                channel=self.channel,
                message="SMTP_USER 또는 SMTP_PASSWORD 환경변수가 설정되지 않음",
            )

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"📰 데일리 테크 다이제스트 ({len(articles)}건)"
            msg["From"] = self.from_email
            msg["To"] = self.to_email

            # Plain text와 HTML 모두 첨부
            plain_part = MIMEText(self._format_plain(articles), "plain", "utf-8")
            html_part = MIMEText(self._format_html(articles), "html", "utf-8")

            msg.attach(plain_part)
            msg.attach(html_part)

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, self.to_email, msg.as_string())

            return NotifyResult(success=True, channel=self.channel)

        except Exception as e:
            return NotifyResult(success=False, channel=self.channel, message=str(e))
