from django.conf import settings
from rest_framework.throttling import SimpleRateThrottle


class AnonymousRequestThrottle(SimpleRateThrottle):
    """
    Applies per-IP throttling for unauthenticated endpoints (e.g., register/login)
    and blocks abusive IPs for a configurable duration.
    """

    scope = "anon_actions"
    block_prefix = "anon_block"

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            return None
        ident = self.get_ident(request)
        self._current_ident = ident
        return self.cache_format % {"scope": self.scope, "ident": ident}

    def allow_request(self, request, view):
        if request.user and request.user.is_authenticated:
            return True

        ident = getattr(self, "_current_ident", self.get_ident(request))
        block_key = f"{self.block_prefix}_{ident}"
        if self.cache.get(block_key):
            return False

        allowed = super().allow_request(request, view)
        if not allowed:
            block_ttl = getattr(settings, "ANON_BLOCK_SECONDS", 300)
            self.cache.set(block_key, True, block_ttl)
        return allowed
