from rest_framework.throttling import SimpleRateThrottle

from randomchat.models import RandomChatQueueEntry
from randomchat.utils import end_random_sessions_for


class RandomChatThrottle(SimpleRateThrottle):
    scope = "randomchat_second"
    block_key_prefix = "randomchat_block"

    def get_cache_key(self, request, _view):
        if request.user and request.user.is_authenticated:
            ident = f"user-{request.user.pk}"
        else:
            ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}

    def _blocked_cache_key(self, ident):
        return f"{self.block_key_prefix}_{ident}"

    def allow_request(self, request, view):
        ident = f"user-{request.user.pk}" if request.user and request.user.is_authenticated else self.get_ident(request)
        if self.cache.get(self._blocked_cache_key(ident)):
            return False

        allowed = super().allow_request(request, view)
        if not allowed:
            if request.user and request.user.is_authenticated:
                end_random_sessions_for(request.user)
                RandomChatQueueEntry.objects.filter(user=request.user).delete()
            else:
                self.cache.set(self._blocked_cache_key(ident), True, 300)
        return allowed

    def allow_request(self, request, view):
        allowed = super().allow_request(request, view)
        if not allowed and request.user and request.user.is_authenticated:
            end_random_sessions_for(request.user)
            RandomChatQueueEntry.objects.filter(user=request.user).delete()
        return allowed
