# Tech Digest Bot

국내 개발자 커뮤니티와 테크블로그에서 관심 키워드에 맞는 글을 수집하여 **매일 오전 8시**에 이메일/Slack으로 보내주는 서비스입니다.

## 기능

- 📧 **이메일 / Slack 알림** 선택
- 🔍 **키워드 필터링** (선택)
- 📰 **9개 국내 소스** 지원

## 지원 소스

| 커뮤니티 | 테크블로그 |
|----------|------------|
| GeekNews | 카카오 테크 |
| 요즘IT | 토스 테크 |
| velog | 당근 테크 |
| | 라인 테크 |
| | NHN 밋업 |
| | 하이퍼커넥트 |

## 로컬 실행

```bash
# 설치
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 환경변수 설정
export SMTP_USER="your@gmail.com"
export SMTP_PASSWORD="앱비밀번호"

# 서버 실행
python -m src.server
```

http://localhost:8000 접속

## 배포 (Railway)

1. [Railway](https://railway.app) 가입
2. New Project → Deploy from GitHub repo
3. 환경변수 설정:
   - `SMTP_USER`: Gmail 주소
   - `SMTP_PASSWORD`: Gmail 앱 비밀번호
4. Deploy

## 프로젝트 구조

```
├── src/
│   ├── app.py              # FastAPI 웹 앱
│   ├── server.py           # 서버 + 스케줄러
│   ├── scheduler.py        # 다이제스트 발송
│   ├── db.py               # SQLite DB
│   ├── templates/          # HTML 템플릿
│   ├── sources/            # 뉴스 소스
│   └── notifiers/          # 알림 채널
├── data/                   # DB 파일 (자동 생성)
├── Procfile                # Railway 배포
└── requirements.txt
```

## 라이선스

MIT
