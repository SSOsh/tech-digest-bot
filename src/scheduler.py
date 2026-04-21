"""스케줄러 - 매일 08시 발송"""
import json
import os
import time
from datetime import datetime, timedelta, timezone

from src.db import Subscription, get_all_subscriptions, update_last_sent_at
from src.filter import filter_articles
from src.notifiers import EmailNotifier, SlackNotifier
from src.sources import get_all_sources, get_source


def fetch_articles_for_subscription(sub: Subscription) -> list:
    """구독 설정에 맞는 기사 수집"""
    source_ids = [s.strip() for s in sub.sources.split(",") if s.strip()]
    if not source_ids:
        source_ids = list(get_all_sources().keys())

    # source_options 파싱
    options = {}
    if sub.source_options:
        try:
            options = json.loads(sub.source_options)
        except json.JSONDecodeError:
            print(f"[WARN] source_options 파싱 실패: {sub.source_options}")

    # 키워드 파싱
    keywords = [k.strip() for k in sub.keywords.split(",") if k.strip()] if sub.keywords else []

    articles = []
    seen_urls = set()  # URL 기반 중복 제거

    for source_id in source_ids:
        source = get_source(source_id)
        if source:
            try:
                # 소스별 옵션 가져오기
                source_opt = options.get(source_id, {})
                top_n = source_opt.get("top_n")
                limit = source_opt.get("limit")

                # 소스 타입에 따라 적절한 파라미터 전달 (키워드 포함)
                if source.supports_points:
                    fetched = source.fetch_articles(hours=24, top_n=top_n, keywords=keywords)
                else:
                    fetched = source.fetch_articles(hours=24, limit=limit, keywords=keywords)

                for article in fetched:
                    if article.url not in seen_urls:
                        seen_urls.add(article.url)
                        articles.append(article)
            except Exception as e:
                print(f"[ERROR] {source_id} 수집 실패: {e}")

    return articles


def send_digest(sub: Subscription, articles: list, max_retries: int = 3) -> bool:
    """다이제스트 발송 (재시도 포함)"""
    # min_points 필터링만 수행 (키워드는 이미 Source 레벨에서 필터링됨)
    filtered = []
    for article in articles:
        # 최소 점수 체크 (GeekNews처럼 점수 지원하는 소스만)
        if article.points is not None and article.points < sub.min_points:
            continue
        filtered.append(article)

    # 점수 있는 것 우선, 그 다음 시간순 정렬
    def sort_key(a):
        return (
            -(a.points or 0),  # 점수 높은 순
            -(a.published_at.timestamp() if a.published_at else 0),  # 최신순
        )
    filtered.sort(key=sort_key)

    # 알림 전송 (재시도 포함)
    if sub.email:
        notifier = EmailNotifier(sub.email)
    elif sub.slack_webhook:
        notifier = SlackNotifier(sub.slack_webhook)
    else:
        return False

    # Exponential backoff로 재시도
    for attempt in range(max_retries):
        result = notifier.send(filtered, f"sub_{sub.id}")
        if result.success:
            return True

        if attempt < max_retries - 1:
            # 재시도 전 대기 (1초, 2초, 4초)
            wait_time = 2**attempt
            print(f"[WARN] 발송 실패 ({attempt + 1}/{max_retries}), {wait_time}초 후 재시도: {result.message}")
            time.sleep(wait_time)
        else:
            print(f"[ERROR] 발송 최종 실패: {result.message}")

    return False


def run_daily_digest():
    """전체 구독자에게 다이제스트 발송"""
    print(f"[INFO] 다이제스트 발송 시작: {datetime.now()}")

    subscriptions = get_all_subscriptions()
    print(f"[INFO] 총 {len(subscriptions)}명 구독자")

    success_count = 0
    fail_count = 0
    skip_count = 0

    now = datetime.now(timezone.utc)

    for sub in subscriptions:
        try:
            # 중복 발송 방지: 지난 20시간 이내에 발송한 경우 스킵
            if sub.last_sent_at:
                # last_sent_at이 문자열인 경우 파싱
                if isinstance(sub.last_sent_at, str):
                    last_sent = datetime.fromisoformat(sub.last_sent_at.replace('Z', '+00:00'))
                else:
                    last_sent = sub.last_sent_at
                    # naive datetime을 UTC로 간주
                    if last_sent.tzinfo is None:
                        last_sent = last_sent.replace(tzinfo=timezone.utc)

                time_since_last = now - last_sent
                if time_since_last < timedelta(hours=20):
                    print(f"[INFO] 스킵: {sub.email or sub.slack_webhook[:30]} (마지막 발송: {time_since_last.seconds // 3600}시간 전)")
                    skip_count += 1
                    continue

            print(f"[INFO] 처리 중: {sub.email or sub.slack_webhook[:30]}...")

            articles = fetch_articles_for_subscription(sub)
            print(f"[INFO] {len(articles)}개 기사 수집")

            if send_digest(sub, articles):
                print(f"[INFO] 발송 성공")
                update_last_sent_at(sub.id)
                success_count += 1
            else:
                print(f"[ERROR] 발송 실패")
                fail_count += 1

        except Exception as e:
            print(f"[ERROR] 처리 실패: {e}")
            fail_count += 1

    print(f"[INFO] 완료 - 성공: {success_count}, 실패: {fail_count}, 스킵: {skip_count}")
    return success_count, fail_count


if __name__ == "__main__":
    # DB 초기화
    from src.db import init_db
    init_db()

    # 다이제스트 발송
    run_daily_digest()
