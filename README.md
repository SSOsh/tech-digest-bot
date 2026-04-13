# Tech Digest Bot

국내 개발자 커뮤니티와 테크블로그에서 관심 키워드에 맞는 글을 수집하여 Slack/이메일로 알려주는 봇입니다.

## 지원 소스

| ID | 이름 | 유형 |
|----|------|------|
| `geeknews` | GeekNews | 커뮤니티 (점수 지원) |
| `yozm` | 요즘IT | 매거진 |
| `velog` | velog | 블로그 플랫폼 |
| `kakao` | 카카오 테크 | 테크블로그 |
| `toss` | 토스 테크 | 테크블로그 |
| `daangn` | 당근 테크 | 테크블로그 |
| `line` | 라인 테크 | 테크블로그 |
| `nhn` | NHN 밋업 | 테크블로그 |
| `hyperconnect` | 하이퍼커넥트 | 테크블로그 |

## 설치

```bash
git clone https://github.com/your-username/tech-digest-bot.git
cd tech-digest-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 설정

### 1. users_config.yaml 수정

```yaml
users:
  - id: user1
    slack: true                    # Slack 알림
    email: user@example.com        # 이메일 알림 (선택)

    sources:                       # 구독할 소스
      - geeknews
      - yozm
      - kakao

    keywords:                      # 관심 키워드
      - python
      - kubernetes
      - ai

    min_points: 20                 # GeekNews 최소 점수
    hours: 72                      # 수집 기간 (시간)
```

### 2. 환경변수 설정

**Slack**
```bash
export SLACK_WEBHOOK_USER1="https://hooks.slack.com/services/..."
```

**이메일 (Gmail)**
```bash
export SMTP_USER="your@gmail.com"
export SMTP_PASSWORD="xxxx xxxx xxxx xxxx"  # 앱 비밀번호
```

## 실행

```bash
source .venv/bin/activate
python -m src.main
```

## GitHub Actions 자동화

`.github/workflows/daily.yml`이 매일 오전 9시(KST)에 실행됩니다.

### GitHub Secrets 설정

Repository Settings → Secrets and variables → Actions에서 추가:

- `SLACK_WEBHOOK_USER1`: Slack Webhook URL
- `SMTP_USER`: Gmail 주소 (이메일 사용 시)
- `SMTP_PASSWORD`: Gmail 앱 비밀번호 (이메일 사용 시)

### Gmail 앱 비밀번호 발급

1. Google 계정 → 보안 → 2단계 인증 활성화
2. 앱 비밀번호 → 앱 선택: 메일
3. 생성된 16자리 비밀번호 사용

## 프로젝트 구조

```
├── src/
│   ├── sources/          # 뉴스 소스
│   │   ├── base.py
│   │   ├── geeknews.py
│   │   ├── rss.py
│   │   └── registry.py
│   ├── notifiers/        # 알림 채널
│   │   ├── base.py
│   │   ├── slack.py
│   │   └── email.py
│   ├── config.py
│   ├── filter.py
│   └── main.py
├── users_config.yaml
├── requirements.txt
└── .github/workflows/
```

## 라이선스

MIT
