from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed


class ExpiringTokenAuthentication(TokenAuthentication):
    """
    TokenAuthentication 확장 버전.
    토큰 생성 후 지정된 TTL(기본 30분)이 지나면 토큰을 폐기하고 인증을 거부합니다.
    """

    def authenticate_credentials(self, key):
        model = self.get_model()
        try:
            token = model.objects.select_related("user").get(key=key)
        except model.DoesNotExist as exc:
            raise AuthenticationFailed("유효하지 않은 토큰입니다.") from exc

        if not token.user.is_active:
            raise AuthenticationFailed("비활성화된 사용자입니다.")

        ttl = getattr(settings, "AUTH_TOKEN_TTL_SECONDS", 1800)
        expires_at = token.created + timedelta(seconds=ttl)
        if timezone.now() >= expires_at:
            token.delete()
            raise AuthenticationFailed("로그인 세션이 만료되었습니다. 다시 로그인해 주세요.")

        return (token.user, token)
