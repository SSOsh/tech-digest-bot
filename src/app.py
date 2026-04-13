"""FastAPI 웹 앱"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.db import (
    Subscription,
    add_subscription,
    delete_subscription,
    get_all_subscriptions,
    get_subscription_by_email,
    init_db,
)
from src.sources.registry import get_all_sources


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작 시 DB 초기화"""
    init_db()
    yield


app = FastAPI(title="Tech Digest Bot", lifespan=lifespan)

# 템플릿 설정
templates = Jinja2Templates(directory="src/templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """메인 페이지"""
    sources = get_all_sources()
    subscriptions = get_all_subscriptions()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "sources": sources,
            "subscriptions": subscriptions,
        },
    )


@app.post("/subscribe")
async def subscribe(
    notify_type: str = Form(...),
    email: str = Form(None),
    slack_webhook: str = Form(None),
    keywords: str = Form(""),
    sources: list[str] = Form([]),
    min_points: int = Form(0),
):
    """구독 등록"""
    # 유효성 검사
    if notify_type == "email" and not email:
        return RedirectResponse("/?error=이메일을 입력해주세요", status_code=303)
    if notify_type == "slack" and not slack_webhook:
        return RedirectResponse("/?error=Slack Webhook URL을 입력해주세요", status_code=303)

    # 중복 체크 (이메일인 경우)
    if email and get_subscription_by_email(email):
        return RedirectResponse("/?error=이미 등록된 이메일입니다", status_code=303)

    sub = Subscription(
        id=None,
        email=email if notify_type == "email" else None,
        slack_webhook=slack_webhook if notify_type == "slack" else None,
        keywords=keywords.strip(),
        sources=",".join(sources) if sources else "",
        min_points=min_points,
    )

    add_subscription(sub)

    return RedirectResponse("/?success=구독이 등록되었습니다", status_code=303)


@app.post("/unsubscribe/{sub_id}")
async def unsubscribe(sub_id: int):
    """구독 취소"""
    delete_subscription(sub_id)
    return RedirectResponse("/?success=구독이 취소되었습니다", status_code=303)


@app.get("/health")
async def health():
    """헬스 체크"""
    return {"status": "ok"}
