"""스케줄러 - 매일 08시 발송"""
import os
from datetime import datetime

from src.db import Subscription, get_all_subscriptions
from src.filter import filter_articles
from src.notifiers import EmailNotifier, SlackNotifier
from src.sources import get_all_sources, get_source


def fetch_articles_for_subscription(sub: Subscription) -> list:
    """구독 설정에 맞는 기사 수집"""
    source_ids = [s.strip() for s in sub.sources.split(",") if s.strip()]
    if not source_ids:
        source_ids = list(get_all_sources().keys())

    articles = []
    for source_id in source_ids:
        source = get_source(source_id)
        if source:
            try:
                fetched = source.fetch_articles(hours=24)
                articles.extend(fetched)
            except Exception as e:
                print(f"[ERROR] {source_id} 수집 실패: {e}")

    return articles


def send_digest(sub: Subscription, articles: list) -> bool:
    """다이제스트 발송"""
    # 키워드 필터링
    keywords = [k.strip() for k in sub.keywords.split(",") if k.strip()]
    filtered = filter_articles(articles, keywords, sub.min_points)

    # 알림 전송
    if sub.email:
        notifier = EmailNotifier(sub.email)
    elif sub.slack_webhook:
        notifier = SlackNotifier(sub.slack_webhook)
    else:
        return False

    result = notifier.send(filtered, f"sub_{sub.id}")
    return result.success


def run_daily_digest():
    """전체 구독자에게 다이제스트 발송"""
    print(f"[INFO] 다이제스트 발송 시작: {datetime.now()}")

    subscriptions = get_all_subscriptions()
    print(f"[INFO] 총 {len(subscriptions)}명 구독자")

    success_count = 0
    fail_count = 0

    for sub in subscriptions:
        try:
            print(f"[INFO] 처리 중: {sub.email or sub.slack_webhook[:30]}...")

            articles = fetch_articles_for_subscription(sub)
            print(f"[INFO] {len(articles)}개 기사 수집")

            if send_digest(sub, articles):
                print(f"[INFO] 발송 성공")
                success_count += 1
            else:
                print(f"[ERROR] 발송 실패")
                fail_count += 1

        except Exception as e:
            print(f"[ERROR] 처리 실패: {e}")
            fail_count += 1

    print(f"[INFO] 완료 - 성공: {success_count}, 실패: {fail_count}")
    return success_count, fail_count


if __name__ == "__main__":
    # DB 초기화
    from src.db import init_db
    init_db()

    # 다이제스트 발송
    run_daily_digest()
