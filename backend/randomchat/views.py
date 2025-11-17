import random

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from randomchat.models import RandomChatMessage, RandomChatQueueEntry, RandomChatSession
from randomchat.serializers import RandomChatMessageSerializer
from randomchat.throttles import RandomChatThrottle
from randomchat.utils import (
    RANDOM_CHAT_DEFAULT_LIMIT,
    RANDOM_CHAT_MAX_LIMIT,
    build_random_chat_state,
    end_random_sessions_for,
    get_active_random_session,
    perform_randomchat_housekeeping,
)


class RandomChatStateView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [RandomChatThrottle]

    def _get_limit(self, request):
        try:
            limit = int(request.query_params.get("limit", RANDOM_CHAT_DEFAULT_LIMIT))
        except (TypeError, ValueError):
            limit = RANDOM_CHAT_DEFAULT_LIMIT
        return max(1, min(limit, RANDOM_CHAT_MAX_LIMIT))

    def get(self, request):
        perform_randomchat_housekeeping()
        limit = self._get_limit(request)
        payload = build_random_chat_state(request, limit)
        return Response(payload, status=status.HTTP_200_OK)


class RandomChatQueueView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [RandomChatThrottle]

    def post(self, request):
        perform_randomchat_housekeeping()
        entry, created = RandomChatQueueEntry.objects.get_or_create(user=request.user)
        if not created:
            entry.joined_at = timezone.now()
            entry.save(update_fields=["joined_at"])
        payload = build_random_chat_state(request)
        return Response(payload, status=status.HTTP_200_OK)

    def delete(self, request):
        perform_randomchat_housekeeping()
        RandomChatQueueEntry.objects.filter(user=request.user).delete()
        end_random_sessions_for(request.user)
        return Response({"detail": "랜덤 채팅 대기열에서 나갔습니다."}, status=status.HTTP_200_OK)


class RandomChatMatchView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [RandomChatThrottle]

    def post(self, request):
        perform_randomchat_housekeeping()
        with transaction.atomic():
            try:
                own_entry = RandomChatQueueEntry.objects.select_for_update().get(user=request.user)
            except RandomChatQueueEntry.DoesNotExist:
                own_entry = RandomChatQueueEntry.objects.create(user=request.user)
            candidates = list(
                RandomChatQueueEntry.objects.select_for_update().exclude(user=request.user)
            )
            if not candidates:
                return Response(
                    {"detail": "대기 중인 다른 이용자가 없습니다. 잠시만 기다려 주세요."},
                    status=status.HTTP_202_ACCEPTED,
                )
            partner_entry = random.choice(candidates)
            partner_user = partner_entry.user
            partner_entry.delete()
            own_entry.delete()

        end_random_sessions_for(request.user)
        end_random_sessions_for(partner_user)
        RandomChatSession.objects.create(participant_a=request.user, participant_b=partner_user)
        payload = build_random_chat_state(request)
        return Response(payload, status=status.HTTP_201_CREATED)


class RandomChatMessageView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [RandomChatThrottle]

    def _ensure_session(self, request):
        session = get_active_random_session(request.user)
        if not session:
            raise PermissionDenied("랜덤 채팅 세션이 없습니다. 먼저 매칭을 시작해 주세요.")
        return session

    def get(self, request):
        perform_randomchat_housekeeping()
        session = get_active_random_session(request.user)
        if not session:
            return Response({"messages": []}, status=status.HTTP_200_OK)
        limit = RandomChatStateView()._get_limit(request)
        queryset = (
            RandomChatMessage.objects.filter(session=session)
            .order_by("-created_at")[:limit]
        )
        messages = list(queryset)
        messages.reverse()
        serializer = RandomChatMessageSerializer(messages, many=True, context={"request": request})
        return Response({"messages": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request):
        perform_randomchat_housekeeping()
        session = self._ensure_session(request)
        serializer = RandomChatMessageSerializer(
            data=request.data,
            context={"request": request, "session": session},
        )
        serializer.is_valid(raise_exception=True)
        message = serializer.save()
        return Response(
            RandomChatMessageSerializer(message, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )
