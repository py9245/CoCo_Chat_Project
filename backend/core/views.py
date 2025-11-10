from django.contrib.auth import authenticate, get_user_model
from django.http import JsonResponse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import ChatMessage, Message
from core.serializers import (
    ChatMessageSerializer,
    LoginSerializer,
    MessageSerializer,
    RegisterSerializer,
    UserSerializer,
)

User = get_user_model()


def healthz(_request):
    return JsonResponse({"ok": True})


class MessageListView(APIView):
    """Expose Message rows so the Vue frontend can render dynamic content."""

    def get(self, _request):
        messages = Message.objects.all()
        serializer = MessageSerializer(messages, many=True)
        return Response({"messages": serializer.data})


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {"token": token.key, "user": UserSerializer(user).data},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )
        if not user:
            return Response(
                {"detail": "아이디 또는 비밀번호가 올바르지 않습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user": UserSerializer(user).data})


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"user": UserSerializer(request.user).data})


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        auth_token = getattr(request, "auth", None)
        if isinstance(auth_token, Token):
            auth_token.delete()
        return Response({"detail": "로그아웃되었습니다."})


class ChatMessageListCreateView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    DEFAULT_LIMIT = 50
    MAX_LIMIT = 150

    def get_messages(self, request):
        limit = self.DEFAULT_LIMIT
        try:
            raw = int(request.query_params.get("limit", self.DEFAULT_LIMIT))
            limit = max(1, min(raw, self.MAX_LIMIT))
        except (TypeError, ValueError):
            limit = self.DEFAULT_LIMIT

        queryset = ChatMessage.objects.select_related("user").order_by("-created_at")
        recent = list(queryset[:limit])
        recent.reverse()
        return recent

    def get(self, request):
        messages = self.get_messages(request)
        serializer = ChatMessageSerializer(messages, many=True)
        return Response({"messages": serializer.data})

    def post(self, request):
        serializer = ChatMessageSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
