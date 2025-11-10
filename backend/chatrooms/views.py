from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from chatrooms.models import ChatMessage
from chatrooms.serializers import ChatMessageSerializer


class ChatMessageListCreateView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    DEFAULT_LIMIT = 50
    MAX_LIMIT = 150

    def get_queryset(self, request):
        try:
            limit = int(request.query_params.get("limit", self.DEFAULT_LIMIT))
        except (TypeError, ValueError):
            limit = self.DEFAULT_LIMIT
        limit = max(1, min(limit, self.MAX_LIMIT))
        queryset = ChatMessage.objects.select_related("user").order_by("-created_at")
        recent = list(queryset[:limit])
        recent.reverse()
        return recent

    def get(self, request):
        messages = self.get_queryset(request)
        serializer = ChatMessageSerializer(messages, many=True)
        return Response({"messages": serializer.data})

    def post(self, request):
        if not request.user.is_authenticated:
            return Response({"detail": "로그인이 필요합니다."}, status=401)
        serializer = ChatMessageSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        message = serializer.save()
        return Response(ChatMessageSerializer(message).data, status=201)
