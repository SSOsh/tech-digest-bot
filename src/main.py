"""메인 실행 모듈"""
import sys

from src.config import get_slack_webhook, load_config
from src.filter import filter_articles
from src.notifiers import EmailNotifier, Notifier, SlackNotifier
from src.sources import get_all_sources, get_source
from src.sources.base import Article


def fetch_from_sources(source_ids: list[str], hours: int = 72) -> list[Article]:
    """지정된 소스들에서 기사 수집"""
    all_sources = get_all_sources()

    if not source_ids:
        source_ids = list(all_sources.keys())

    articles = []
    for source_id in source_ids:
        source = get_source(source_id)
        if not source:
            print(f"[WARN] 알 수 없는 소스: {source_id}")
            continue

        try:
            print(f"[INFO] {source.name} 수집 중...")
            fetched = source.fetch_articles(hours=hours)
            print(f"[INFO] {source.name}: {len(fetched)}개 수집")
            articles.extend(fetched)
        except Exception as e:
            print(f"[ERROR] {source.name} 수집 실패: {e}")

    return articles


def get_notifiers(user) -> list[Notifier]:
    """사용자 설정에 따라 알림 채널 목록 반환"""
    notifiers = []

    if user.slack:
        webhook_url = get_slack_webhook(user.id)
        if webhook_url:
            notifiers.append(SlackNotifier(webhook_url))
        else:
            print(f"[WARN] {user.id}: SLACK_WEBHOOK_{user.id.upper()} 환경변수 없음")

    if user.email:
        notifiers.append(EmailNotifier(user.email))

    return notifiers


def main() -> int:
    print("[INFO] Tech Digest Bot 시작")
    print("=" * 50)

    try:
        config = load_config()
    except Exception as e:
        print(f"[ERROR] 설정 로드 실패: {e}")
        return 1

    print(f"[INFO] {len(config.users)}명의 사용자 설정 로드됨")

    success_count = 0
    fail_count = 0

    for user in config.users:
        print(f"\n[INFO] === 사용자: {user.id} ===")

        notifiers = get_notifiers(user)
        if not notifiers:
            print(f"[WARN] 설정된 알림 채널 없음, 스킵")
            continue

        print(f"[INFO] 알림: {', '.join(n.channel for n in notifiers)}")
        print(f"[INFO] 소스: {', '.join(user.sources) if user.sources else '전체'}")
        print(f"[INFO] 키워드: {', '.join(user.keywords) if user.keywords else '없음'}")

        articles = fetch_from_sources(user.sources, hours=user.hours)
        print(f"[INFO] 총 {len(articles)}개 기사 수집")

        if not articles:
            print("[INFO] 수집된 기사 없음")

        filtered = filter_articles(articles, user.keywords, user.min_points)
        print(f"[INFO] 필터링 후: {len(filtered)}개")

        for notifier in notifiers:
            result = notifier.send(filtered, user.id)
            if result.success:
                print(f"[INFO] {result.channel} 전송 성공")
                success_count += 1
            else:
                print(f"[ERROR] {result.channel} 전송 실패: {result.message}")
                fail_count += 1

    print("\n" + "=" * 50)
    print(f"[INFO] 완료 (성공: {success_count}, 실패: {fail_count})")

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
