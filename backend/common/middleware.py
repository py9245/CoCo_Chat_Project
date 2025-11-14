from urllib.parse import parse_qs

from asgiref.sync import sync_to_async
from channels.auth import AuthMiddlewareStack


class TokenAuthMiddleware:
    """
    채널(WebSocket) 연결 시 쿼리스트링 ?token=... 값을 이용해
    DRF Token 인증을 수행하는 미들웨어입니다.
    """

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        scope["user"] = await self.get_user(scope)
        return await self.inner(scope, receive, send)

    @sync_to_async
    def get_user(self, scope):
        from django.contrib.auth.models import AnonymousUser
        from rest_framework.authtoken.models import Token

        query_string = scope.get("query_string", b"").decode()
        params = parse_qs(query_string)
        token_key = params.get("token", [None])[0]
        if not token_key:
            return AnonymousUser()
        try:
            token = Token.objects.select_related("user").get(key=token_key)
            return token.user if token.user.is_active else AnonymousUser()
        except Token.DoesNotExist:
            return AnonymousUser()


def TokenAuthMiddlewareStack(inner):
    return TokenAuthMiddleware(AuthMiddlewareStack(inner))
