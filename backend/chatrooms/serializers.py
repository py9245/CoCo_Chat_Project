from rest_framework import serializers

from chatrooms.models import ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = ["id", "content", "created_at", "is_anonymous", "display_name"]
        read_only_fields = ["id", "created_at", "display_name"]

    def validate_content(self, value):
        text = (value or "").strip()
        if not text:
            raise serializers.ValidationError("내용을 입력해 주세요.")
        if len(text) > 500:
            raise serializers.ValidationError("메시지는 500자 이내로 입력해 주세요.")
        return text

    def create(self, validated_data):
        request = self.context["request"]
        return ChatMessage.objects.create(user=request.user, **validated_data)

    def get_display_name(self, obj):
        return obj.display_name
