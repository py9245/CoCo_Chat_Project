from django.contrib.auth import get_user_model
from rest_framework import serializers

from core.models import ChatMessage, Message

User = get_user_model()


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "title", "body", "created_at"]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(min_length=3, max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)

    def validate_username(self, value: str) -> str:
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("이미 사용 중인 아이디입니다.")
        return value

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("이미 가입된 이메일입니다.")
        return value

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class ChatMessageSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = ["id", "content", "created_at", "is_anonymous", "display_name"]
        read_only_fields = ["id", "created_at", "display_name"]

    def validate_content(self, value: str) -> str:
        text = (value or "").strip()
        if not text:
            raise serializers.ValidationError("내용을 입력해 주세요.")
        if len(text) > 500:
            raise serializers.ValidationError("메시지는 500자 이내로 입력해 주세요.")
        return text

    def create(self, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            raise serializers.ValidationError("로그인이 필요합니다.")
        return ChatMessage.objects.create(user=user, **validated_data)

    def get_display_name(self, obj: ChatMessage) -> str:
        return obj.display_name
