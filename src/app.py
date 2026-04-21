"""FastAPI 웹 앱"""
import json
import os
import re
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
    get_subscription_by_token,
    get_subscription_by_verify_token,
    init_db,
    update_subscription,
    verify_email,
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

# 이메일 검증 정규식
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


def is_valid_email(email: str) -> bool:
    """이메일 형식 검증"""
    return bool(EMAIL_REGEX.match(email))


def send_verification_email(email: str, verify_token: str, request: Request) -> bool:
    """확인 이메일 발송"""
    import os
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    from_email = os.getenv("SMTP_FROM", smtp_user)

    if not smtp_user or not smtp_password:
        print("[ERROR] SMTP 설정이 없어 확인 이메일을 발송할 수 없습니다")
        return False

    verify_url = f"{request.url.scheme}://{request.url.netloc}/verify/{verify_token}"

    html_body = f"""
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h1 style="color: #333;">이메일 주소를 확인해주세요</h1>
        <p>Tech Digest Bot 구독을 완료하려면 아래 버튼을 클릭해주세요:</p>
        <p style="margin: 30px 0;">
            <a href="{verify_url}" style="display: inline-block; padding: 12px 24px; background: #0066cc; color: white; text-decoration: none; border-radius: 8px; font-weight: 500;">이메일 인증하기</a>
        </p>
        <p style="color: #666; font-size: 14px;">
            버튼이 작동하지 않으면 아래 링크를 복사하여 브라우저에 붙여넣으세요:<br>
            <a href="{verify_url}">{verify_url}</a>
        </p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="color: #999; font-size: 12px;">이 이메일을 요청하지 않으셨다면 무시하셔도 됩니다.</p>
    </body>
    </html>
    """

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Tech Digest Bot - 이메일 주소 확인"
        msg["From"] = from_email
        msg["To"] = email

        html_part = MIMEText(html_body, "html", "utf-8")
        msg.attach(html_part)

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(from_email, email, msg.as_string())

        return True

    except Exception as e:
        print(f"[ERROR] 확인 이메일 발송 실패: {e}")
        return False


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
    request: Request,
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

    # 이메일 형식 검증
    if notify_type == "email" and email and not is_valid_email(email):
        return RedirectResponse("/?error=올바른 이메일 형식이 아닙니다", status_code=303)

    # 중복 체크 (이메일인 경우)
    if email and get_subscription_by_email(email):
        return RedirectResponse("/?error=이미 등록된 이메일입니다", status_code=303)

    # source_options 파싱 (폼에서 source_id_top_n, source_id_limit 형식으로 전달)
    form_data = await request.form()
    source_options = {}
    all_sources = get_all_sources()

    for source_id in sources:
        source = all_sources.get(source_id)
        if not source:
            continue

        opts = {}
        if source.supports_points:
            # GeekNews 등 점수 지원 소스: top_n
            top_n_key = f"{source_id}_top_n"
            if top_n_key in form_data and form_data[top_n_key]:
                try:
                    opts["top_n"] = int(form_data[top_n_key])
                except ValueError:
                    pass
        else:
            # RSS 소스: limit
            limit_key = f"{source_id}_limit"
            if limit_key in form_data and form_data[limit_key]:
                try:
                    opts["limit"] = int(form_data[limit_key])
                except ValueError:
                    pass

        if opts:
            source_options[source_id] = opts

    sub = Subscription(
        id=None,
        email=email if notify_type == "email" else None,
        slack_webhook=slack_webhook if notify_type == "slack" else None,
        keywords=keywords.strip(),
        sources=",".join(sources) if sources else "",
        min_points=min_points,
        source_options=json.dumps(source_options) if source_options else None,
    )

    sub_id = add_subscription(sub)

    # 이메일 구독인 경우 확인 이메일 발송
    if notify_type == "email" and email:
        saved_sub = get_subscription_by_email(email)
        if saved_sub and saved_sub.verify_token:
            if send_verification_email(email, saved_sub.verify_token, request):
                return RedirectResponse(
                    "/?success=구독 신청이 완료되었습니다. 이메일을 확인하여 인증을 완료해주세요.", status_code=303
                )
            else:
                return RedirectResponse("/?error=확인 이메일 발송에 실패했습니다. SMTP 설정을 확인해주세요.", status_code=303)

    return RedirectResponse("/?success=구독이 등록되었습니다", status_code=303)


@app.get("/verify/{token}")
async def verify(token: str, request: Request):
    """이메일 인증"""
    sub = get_subscription_by_verify_token(token)
    if not sub:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "message": "유효하지 않은 인증 링크입니다.",
            },
        )

    if sub.email_verified:
        return templates.TemplateResponse(
            "success.html",
            {
                "request": request,
                "message": "이미 인증이 완료된 이메일입니다.",
            },
        )

    if verify_email(sub.id):
        return templates.TemplateResponse(
            "success.html",
            {
                "request": request,
                "message": "이메일 인증이 완료되었습니다! 매일 아침 8시에 다이제스트를 받아보실 수 있습니다.",
            },
        )
    else:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "message": "이메일 인증에 실패했습니다.",
            },
        )


@app.get("/edit/{token}")
async def edit_subscription_page(token: str, request: Request):
    """구독 설정 수정 페이지"""
    sub = get_subscription_by_token(token)
    if not sub:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "message": "유효하지 않은 링크입니다.",
            },
        )

    sources = get_all_sources()

    # source_options 파싱
    import json

    source_options_dict = {}
    if sub.source_options:
        try:
            source_options_dict = json.loads(sub.source_options)
        except json.JSONDecodeError:
            pass

    return templates.TemplateResponse(
        "edit.html",
        {
            "request": request,
            "subscription": sub,
            "sources": sources,
            "source_options": source_options_dict,
        },
    )


@app.post("/edit/{token}")
async def edit_subscription(
    token: str,
    request: Request,
    keywords: str = Form(""),
    sources: list[str] = Form([]),
    min_points: int = Form(0),
):
    """구독 설정 수정 처리"""
    sub = get_subscription_by_token(token)
    if not sub:
        return RedirectResponse("/?error=유효하지 않은 링크입니다", status_code=303)

    # source_options 파싱
    form_data = await request.form()
    source_options = {}
    all_sources = get_all_sources()

    for source_id in sources:
        source = all_sources.get(source_id)
        if not source:
            continue

        opts = {}
        if source.supports_points:
            top_n_key = f"{source_id}_top_n"
            if top_n_key in form_data and form_data[top_n_key]:
                try:
                    opts["top_n"] = int(form_data[top_n_key])
                except ValueError:
                    pass
        else:
            limit_key = f"{source_id}_limit"
            if limit_key in form_data and form_data[limit_key]:
                try:
                    opts["limit"] = int(form_data[limit_key])
                except ValueError:
                    pass

        if opts:
            source_options[source_id] = opts

    # 구독 정보 업데이트
    sub.keywords = keywords.strip()
    sub.sources = ",".join(sources) if sources else ""
    sub.min_points = min_points
    sub.source_options = json.dumps(source_options) if source_options else None

    if update_subscription(sub):
        return RedirectResponse("/?success=구독 설정이 수정되었습니다", status_code=303)
    else:
        return RedirectResponse("/?error=구독 설정 수정에 실패했습니다", status_code=303)


@app.get("/unsubscribe/{token}")
async def unsubscribe(token: str, request: Request):
    """구독 취소 (토큰 기반 인증)"""
    sub = get_subscription_by_token(token)
    if not sub:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "message": "유효하지 않은 구독 취소 링크입니다.",
            },
        )

    if delete_subscription(sub.id, token):
        return templates.TemplateResponse(
            "success.html",
            {
                "request": request,
                "message": "구독이 성공적으로 취소되었습니다.",
            },
        )
    else:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "message": "구독 취소에 실패했습니다.",
            },
        )


@app.post("/test-send/{sub_id}")
async def test_send(sub_id: int):
    """테스트 발송 - 현재 설정으로 즉시 발송"""
    from src.scheduler import fetch_articles_for_subscription, send_digest

    # 구독 정보 조회
    subs = get_all_subscriptions()
    sub = None
    for s in subs:
        if s.id == sub_id:
            sub = s
            break

    if not sub:
        # 미인증 구독도 포함해서 조회
        from src.db import get_connection

        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM subscriptions WHERE id = ? AND active = 1", (sub_id,)
            ).fetchone()

            if row:
                sub = Subscription(
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

    if not sub:
        return RedirectResponse("/?error=구독을 찾을 수 없습니다", status_code=303)

    try:
        # 기사 수집
        articles = fetch_articles_for_subscription(sub)

        # 발송
        if send_digest(sub, articles):
            return RedirectResponse("/?success=테스트 발송이 완료되었습니다", status_code=303)
        else:
            return RedirectResponse("/?error=테스트 발송에 실패했습니다", status_code=303)

    except Exception as e:
        print(f"[ERROR] 테스트 발송 실패: {e}")
        return RedirectResponse(f"/?error=테스트 발송 중 오류가 발생했습니다: {str(e)}", status_code=303)


@app.get("/health")
async def health():
    """헬스 체크"""
    return {"status": "ok"}
