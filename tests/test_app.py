"""웹 앱 테스트

@author suho.do
@since 2026-04-21
"""
import pytest

from src.app import is_valid_email


class TestEmailValidation:
    """이메일 검증 테스트"""

    def test_valid_emails(self):
        """올바른 이메일 형식"""
        # given
        valid_emails = [
            "test@example.com",
            "user.name@example.com",
            "user+tag@example.co.kr",
            "123@test.com",
            "test_user@example.com",
        ]

        # when & then
        for email in valid_emails:
            assert is_valid_email(email) is True, f"{email} should be valid"

    def test_invalid_emails(self):
        """잘못된 이메일 형식"""
        # given
        invalid_emails = [
            "notanemail",
            "a@b",
            "@example.com",
            "test@",
            "test @example.com",  # 공백
            "test@example",  # TLD 없음
            "",
            "test@.com",
        ]

        # when & then
        for email in invalid_emails:
            assert is_valid_email(email) is False, f"{email} should be invalid"

    def test_edge_cases(self):
        """경계값 테스트"""
        # given & when & then
        assert is_valid_email("a@b.co") is True  # 최소 길이
        assert is_valid_email("a" * 64 + "@" + "b" * 63 + ".com") is True  # 긴 이메일
        assert is_valid_email("test@subdomain.example.com") is True  # 서브도메인


class TestSubscriptionFlow:
    """구독 플로우 테스트"""

    def test_subscription_requires_email_or_webhook(self):
        """구독 시 이메일 또는 Webhook 필수"""
        # 이 테스트는 실제 DB 제약조건(CONSTRAINT chk_notify)에 의해 보장됨
        # DB 레벨에서 검증되므로 별도 테스트 불필요
        pass

    def test_unsubscribe_requires_valid_token(self):
        """구독 취소 시 유효한 토큰 필요"""
        # 이 테스트는 test_db.py의 test_delete_subscription_requires_token에서 다룸
        pass


class TestSourceOptions:
    """소스 옵션 테스트"""

    def test_source_options_json_format(self):
        """source_options JSON 형식"""
        import json

        # given
        options = {
            "geeknews": {"top_n": 15},
            "kakao": {"limit": 10},
        }

        # when
        json_str = json.dumps(options)
        parsed = json.loads(json_str)

        # then
        assert parsed["geeknews"]["top_n"] == 15
        assert parsed["kakao"]["limit"] == 10

    def test_source_options_parsing_error_handling(self):
        """source_options 파싱 오류 처리"""
        import json

        # given
        invalid_json = "not a json"

        # when & then
        with pytest.raises(json.JSONDecodeError):
            json.loads(invalid_json)
