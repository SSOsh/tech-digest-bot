"""서버 실행 (스케줄러 포함)"""
import os
from contextlib import asynccontextmanager

import uvicorn
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from src.app import app
from src.db import init_db
from src.scheduler import run_daily_digest

scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app):
    """앱 시작/종료 시 스케줄러 관리"""
    init_db()

    # 매일 08시 (KST = UTC+9, 따라서 UTC 23시)
    scheduler.add_job(
        run_daily_digest,
        CronTrigger(hour=23, minute=0),  # UTC 23:00 = KST 08:00
        id="daily_digest",
        replace_existing=True,
    )
    scheduler.start()
    print("[INFO] 스케줄러 시작 - 매일 08:00 KST 발송")

    yield

    scheduler.shutdown()
    print("[INFO] 스케줄러 종료")


# lifespan 재설정
app.router.lifespan_context = lifespan


def main():
    """서버 실행"""
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "src.server:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("ENV") == "development",
    )


if __name__ == "__main__":
    main()
