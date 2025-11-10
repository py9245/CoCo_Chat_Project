from django.utils.encoding import iri_to_uri
from rest_framework import serializers

from accounts.serializers import UserSerializer
from boards.models import Post
from common.storage import build_file_url


class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    attachment = serializers.FileField(required=False, allow_null=True)
    attachment_url = serializers.SerializerMethodField()
    clear_attachment = serializers.BooleanField(required=False, write_only=True, default=False)

    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "body",
            "attachment",
            "attachment_url",
            "clear_attachment",
            "created_at",
            "author",
        ]
        read_only_fields = ["id", "created_at", "author", "attachment_url"]

    def validate_attachment(self, value):
        if not value:
            return value
        max_size = 5 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("첨부파일은 최대 5MB까지 업로드할 수 있습니다.")
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        if request and request.method == "POST":
            user = request.user
            if not user or not user.is_authenticated:
                raise serializers.ValidationError("로그인이 필요합니다.")
            today_count = Post.objects.for_today(user).count()
            if today_count >= 5:
                raise serializers.ValidationError("하루에 최대 5개의 게시글만 작성할 수 있습니다.")
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        validated_data.pop("clear_attachment", None)
        return Post.objects.create(author=request.user, **validated_data)

    def update(self, instance, validated_data):
        clear_attachment = validated_data.pop("clear_attachment", False)
        attachment = validated_data.get("attachment")

        if clear_attachment and instance.attachment:
            instance.attachment.delete(save=False)
            if "attachment" in validated_data and not attachment:
                validated_data.pop("attachment")

        if attachment and instance.attachment and instance.attachment.name != attachment.name:
            instance.attachment.delete(save=False)

        return super().update(instance, validated_data)

    def get_attachment_url(self, obj):
        if obj.attachment:
            request = self.context.get("request")
            url = build_file_url(obj.attachment)
            if url and request and url.startswith("/"):
                return request.build_absolute_uri(iri_to_uri(url))
            return url
        return None
