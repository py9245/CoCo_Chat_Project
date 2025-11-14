from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import UserProfile
from accounts.serializers import (
    AvatarUploadSerializer,
    DeleteAccountSerializer,
    LoginSerializer,
    PasswordChangeSerializer,
    ProfileSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
)
from common.throttles import AnonymousRequestThrottle


def issue_token_for_user(user):
    Token.objects.filter(user=user).delete()
    return Token.objects.create(user=user)


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonymousRequestThrottle]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        profile = UserProfile.objects.get(user=user)
        token = issue_token_for_user(user)
        return Response(
            {"token": token.key, "profile": ProfileSerializer(profile, context={"request": request}).data},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonymousRequestThrottle]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        profile = UserProfile.objects.get(user=user)
        token = issue_token_for_user(user)
        return Response(
            {"token": token.key, "profile": ProfileSerializer(profile, context={"request": request}).data},
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        auth_token = getattr(request, "auth", None)
        if isinstance(auth_token, Token):
            auth_token.delete()
        return Response({"detail": "로그아웃되었습니다."})


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.profile
        serializer = ProfileSerializer(profile, context={"request": request})
        return Response({"profile": serializer.data})


class ProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        profile = request.user.profile
        serializer = ProfileUpdateSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"profile": ProfileSerializer(profile, context={"request": request}).data})


class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        token = issue_token_for_user(request.user)
        return Response({"detail": "비밀번호가 변경되었습니다.", "token": token.key})


class AvatarUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        profile = request.user.profile
        serializer = AvatarUploadSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"profile": ProfileSerializer(profile, context={"request": request}).data})


class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DeleteAccountSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = request.user
        Token.objects.filter(user=user).delete()
        user.delete()
        return Response({"detail": "회원 탈퇴가 완료되었습니다."}, status=status.HTTP_200_OK)
