"""데이터베이스 모델"""
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
                CONSTRAINT chk_notify CHECK (email IS NOT NULL OR slack_webhook IS NOT NULL)
            )
        """)
        conn.commit()


@contextmanager
def get_connection():
    """DB 연결"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def add_subscription(sub: Subscription) -> int:
    """구독 추가"""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO subscriptions (email, slack_webhook, keywords, sources, min_points)
            VALUES (?, ?, ?, ?, ?)
            """,
            (sub.email, sub.slack_webhook, sub.keywords, sub.sources, sub.min_points),
        )
        conn.commit()
        return cursor.lastrowid


def get_all_subscriptions() -> list[Subscription]:
    """모든 활성 구독 조회"""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM subscriptions WHERE active = 1"
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
            )
            for row in rows
        ]


def delete_subscription(sub_id: int) -> bool:
    """구독 삭제 (비활성화)"""
    with get_connection() as conn:
        cursor = conn.execute(
            "UPDATE subscriptions SET active = 0 WHERE id = ?",
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
            )
        return None
