import re

from rest_framework import serializers

from randomchat.models import RandomChatMessage, RandomChatSession


PHONE_PATTERN = re.compile(r"010-\d{4}-\d{4}")


class RandomChatSessionSerializer(serializers.ModelSerializer):
    partner_alias = serializers.SerializerMethodField()

    class Meta:
        model = RandomChatSession
        fields = ["id", "started_at", "partner_alias"]
        read_only_fields = fields

    def get_partner_alias(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        return obj.alias_for(user)


class RandomChatMessageSerializer(serializers.ModelSerializer):
    from_self = serializers.SerializerMethodField()

    class Meta:
        model = RandomChatMessage
        fields = ["id", "content", "created_at", "from_self"]
        read_only_fields = ["id", "created_at", "from_self"]

    def get_from_self(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        return user and obj.sender_id == user.id

    def validate_content(self, value):
        text = (value or "").strip()
        if not text:
            raise serializers.ValidationError("메시지를 입력해 주세요.")
        if len(text) > 500:
            raise serializers.ValidationError("메시지는 500자 이내로 입력해 주세요.")
        if PHONE_PATTERN.search(text):
            raise serializers.ValidationError("전화번호 형식(010-0000-0000)은 전송할 수 없습니다.")
        return text

    def create(self, validated_data):
        request = self.context["request"]
        session = self.context["session"]
        return RandomChatMessage.objects.create(
            session=session,
            sender=request.user,
            **validated_data,
        )
