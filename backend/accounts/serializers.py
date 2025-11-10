from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from accounts.models import UserProfile
from common.storage import build_file_url


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ["user", "display_name", "bio", "avatar_url", "updated_at"]
        read_only_fields = ["updated_at"]

    def get_avatar_url(self, obj):
        if obj.avatar:
            request = self.context.get("request")
            url = build_file_url(obj.avatar)
            if request and url and url.startswith("/"):
                return request.build_absolute_uri(url)
            return url
        return None


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(min_length=3, max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    name = serializers.CharField(min_length=2, max_length=5)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("이미 사용 중인 아이디입니다.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("이미 가입된 이메일입니다.")
        return value

    def validate_name(self, value):
        stripped = value.strip()
        if not stripped:
            raise serializers.ValidationError("이름을 입력해 주세요.")
        if not all("가" <= ch <= "힣" for ch in stripped):
            raise serializers.ValidationError("이름은 한글 2~5글자만 입력할 수 있습니다.")
        if not (2 <= len(stripped) <= 5):
            raise serializers.ValidationError("이름은 한글 2~5글자만 입력할 수 있습니다.")
        return stripped

    def create(self, validated_data):
        name = validated_data.pop("name")
        return User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=name,
        )


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")
        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError("아이디 또는 비밀번호가 올바르지 않습니다.")
        attrs["user"] = user
        return attrs


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["display_name", "bio"]


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        user = self.context["request"].user
        if not user.check_password(attrs["current_password"]):
            raise serializers.ValidationError({"current_password": "현재 비밀번호가 일치하지 않습니다."})
        validate_password(attrs["new_password"], user=user)
        return attrs


class AvatarUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["avatar"]

    def validate_avatar(self, value):
        max_size = 200 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("아바타는 최대 200KB까지 업로드할 수 있습니다.")
        return value


class DeleteAccountSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        request = self.context["request"]
        user = request.user
        if not user.check_password(attrs["password"]):
            raise serializers.ValidationError({"password": "비밀번호가 일치하지 않습니다."})
        return attrs
