"""데이터베이스 모델"""
import secrets
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "subscriptions.db"


@dataclass
class Subscription:
    """구독 정보"""
    id: int | None
    email: str | None
    slack_webhook: str | None
    keywords: str  # 쉼표로 구분
    sources: str  # 쉼표로 구분
    min_points: int
    created_at: datetime | None = None
    active: bool = True
    unsubscribe_token: str | None = None
    source_options: str | None = None  # JSON 형식의 소스별 옵션
    last_sent_at: datetime | None = None  # 마지막 발송 시간
    email_verified: bool = False  # 이메일 인증 여부
    verify_token: str | None = None  # 이메일 인증 토큰


def init_db():
    """DB 초기화"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT,
                slack_webhook TEXT,
                keywords TEXT DEFAULT '',
                sources TEXT DEFAULT '',
                min_points INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                active BOOLEAN DEFAULT 1,
                unsubscribe_token TEXT,
                source_options TEXT,
                last_sent_at TIMESTAMP,
                email_verified BOOLEAN DEFAULT 0,
                verify_token TEXT,
                CONSTRAINT chk_notify CHECK (email IS NOT NULL OR slack_webhook IS NOT NULL)
            )
        """)

        # 마이그레이션: 컬럼 추가 (없는 경우)
        cursor = conn.execute("PRAGMA table_info(subscriptions)")
        columns = [row[1] for row in cursor.fetchall()]

        if "unsubscribe_token" not in columns:
            conn.execute("ALTER TABLE subscriptions ADD COLUMN unsubscribe_token TEXT")
            # 기존 레코드에 토큰 생성
            conn.execute("""
                UPDATE subscriptions
                SET unsubscribe_token = lower(hex(randomblob(16)))
                WHERE unsubscribe_token IS NULL
            """)

        if "source_options" not in columns:
            conn.execute("ALTER TABLE subscriptions ADD COLUMN source_options TEXT")

        if "last_sent_at" not in columns:
            conn.execute("ALTER TABLE subscriptions ADD COLUMN last_sent_at TIMESTAMP")

        if "email_verified" not in columns:
            conn.execute("ALTER TABLE subscriptions ADD COLUMN email_verified BOOLEAN DEFAULT 0")
            # 기존 Slack 구독은 인증된 것으로 간주, 기존 이메일 구독도 인증된 것으로 간주
            conn.execute("UPDATE subscriptions SET email_verified = 1")

        if "verify_token" not in columns:
            conn.execute("ALTER TABLE subscriptions ADD COLUMN verify_token TEXT")

        conn.commit()


@contextmanager
def get_connection():
    """DB 연결 (WAL 모드 활성화로 동시성 개선)"""
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    # WAL 모드 활성화 (Write-Ahead Logging)
    # 읽기와 쓰기가 동시에 가능하도록 개선
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
    finally:
        conn.close()


def add_subscription(sub: Subscription) -> int:
    """구독 추가"""
    # 구독 취소 토큰 생성
    if not sub.unsubscribe_token:
        sub.unsubscribe_token = secrets.token_urlsafe(32)

    # 이메일 구독인 경우 인증 토큰 생성
    if sub.email and not sub.verify_token:
        sub.verify_token = secrets.token_urlsafe(32)
        sub.email_verified = False
    elif sub.slack_webhook:
        # Slack 구독은 인증 불필요
        sub.email_verified = True

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO subscriptions (email, slack_webhook, keywords, sources, min_points, unsubscribe_token, source_options, email_verified, verify_token)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sub.email,
                sub.slack_webhook,
                sub.keywords,
                sub.sources,
                sub.min_points,
                sub.unsubscribe_token,
                sub.source_options,
                sub.email_verified,
                sub.verify_token,
            ),
        )
        conn.commit()
        return cursor.lastrowid


def get_all_subscriptions() -> list[Subscription]:
    """모든 활성 구독 조회 (인증된 구독만)"""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM subscriptions WHERE active = 1 AND email_verified = 1"
        ).fetchall()

        return [
            Subscription(
                id=row["id"],
                email=row["email"],
                slack_webhook=row["slack_webhook"],
                keywords=row["keywords"],
                sources=row["sources"],
                min_points=row["min_points"],
                created_at=row["created_at"],
                active=row["active"],
                unsubscribe_token=row.get("unsubscribe_token"),
                source_options=row.get("source_options"),
                last_sent_at=row.get("last_sent_at"),
                email_verified=row.get("email_verified", False),
                verify_token=row.get("verify_token"),
            )
            for row in rows
        ]


def delete_subscription(sub_id: int, token: str) -> bool:
    """구독 삭제 (비활성화) - 토큰 검증 필요"""
    with get_connection() as conn:
        cursor = conn.execute(
            "UPDATE subscriptions SET active = 0 WHERE id = ? AND unsubscribe_token = ?",
            (sub_id, token),
        )
        conn.commit()
        return cursor.rowcount > 0


def get_subscription_by_token(token: str) -> Subscription | None:
    """토큰으로 구독 조회"""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM subscriptions WHERE unsubscribe_token = ? AND active = 1",
            (token,),
        ).fetchone()

        if row:
            return Subscription(
                id=row["id"],
                email=row["email"],
                slack_webhook=row["slack_webhook"],
                keywords=row["keywords"],
                sources=row["sources"],
                min_points=row["min_points"],
                created_at=row["created_at"],
                active=row["active"],
                unsubscribe_token=row.get("unsubscribe_token"),
                source_options=row.get("source_options"),
                last_sent_at=row.get("last_sent_at"),
                email_verified=row.get("email_verified", False),
                verify_token=row.get("verify_token"),
            )
        return None


def get_subscription_by_verify_token(token: str) -> Subscription | None:
    """인증 토큰으로 구독 조회"""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM subscriptions WHERE verify_token = ? AND active = 1",
            (token,),
        ).fetchone()

        if row:
            return Subscription(
                id=row["id"],
                email=row["email"],
                slack_webhook=row["slack_webhook"],
                keywords=row["keywords"],
                sources=row["sources"],
                min_points=row["min_points"],
                created_at=row["created_at"],
                active=row["active"],
                unsubscribe_token=row.get("unsubscribe_token"),
                source_options=row.get("source_options"),
                last_sent_at=row.get("last_sent_at"),
                email_verified=row.get("email_verified", False),
                verify_token=row.get("verify_token"),
            )
        return None


def verify_email(sub_id: int) -> bool:
    """이메일 인증 완료"""
    with get_connection() as conn:
        cursor = conn.execute(
            "UPDATE subscriptions SET email_verified = 1 WHERE id = ?",
            (sub_id,),
        )
        conn.commit()
        return cursor.rowcount > 0


def update_subscription(sub: Subscription) -> bool:
    """구독 정보 업데이트"""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE subscriptions
            SET keywords = ?, sources = ?, min_points = ?, source_options = ?
            WHERE id = ?
            """,
            (sub.keywords, sub.sources, sub.min_points, sub.source_options, sub.id),
        )
        conn.commit()
        return cursor.rowcount > 0


def update_last_sent_at(sub_id: int) -> bool:
    """마지막 발송 시간 업데이트"""
    with get_connection() as conn:
        cursor = conn.execute(
            "UPDATE subscriptions SET last_sent_at = CURRENT_TIMESTAMP WHERE id = ?",
            (sub_id,),
        )
        conn.commit()
        return cursor.rowcount > 0


def get_subscription_by_email(email: str) -> Subscription | None:
    """이메일로 구독 조회"""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM subscriptions WHERE email = ? AND active = 1",
            (email,),
        ).fetchone()

        if row:
            return Subscription(
                id=row["id"],
                email=row["email"],
                slack_webhook=row["slack_webhook"],
                keywords=row["keywords"],
                sources=row["sources"],
                min_points=row["min_points"],
                created_at=row["created_at"],
                active=row["active"],
                unsubscribe_token=row.get("unsubscribe_token"),
                source_options=row.get("source_options"),
                last_sent_at=row.get("last_sent_at"),
                email_verified=row.get("email_verified", False),
                verify_token=row.get("verify_token"),
            )
        return None
