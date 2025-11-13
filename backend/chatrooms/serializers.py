from rest_framework import serializers

from chatrooms.models import ChatMessage, ChatRoom


class ChatRoomSerializer(serializers.ModelSerializer):
    owner_username = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()
    is_member = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = [
            "id",
            "name",
            "capacity",
            "is_private",
            "owner_username",
            "member_count",
            "created_at",
            "is_member",
        ]
        read_only_fields = fields

    def get_owner_username(self, obj):
        return obj.owner.username if obj.owner else None

    def get_member_count(self, obj):
        annotated_count = getattr(obj, "current_members", None)
        if annotated_count is not None:
            return annotated_count
        return obj.memberships.count()

    def get_is_member(self, obj):
        request = self.context.get("request")
        member_room_ids = self.context.get("member_room_ids")
        if member_room_ids is not None:
            return obj.id in member_room_ids
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        return obj.memberships.filter(user=user).exists()


class ChatRoomCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = ChatRoom
        fields = ["name", "capacity", "is_private", "password"]

    def validate_name(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("채팅방 이름을 입력해 주세요.")
        if ChatRoom.objects.filter(name__iexact=cleaned).exists():
            raise serializers.ValidationError("이미 존재하는 채팅방 이름입니다.")
        return cleaned

    def validate_capacity(self, value):
        if value < ChatRoom.MIN_CAPACITY or value > ChatRoom.MAX_CAPACITY:
            raise serializers.ValidationError(
                f"채팅방 정원은 {ChatRoom.MIN_CAPACITY}~{ChatRoom.MAX_CAPACITY}명 사이로 설정해 주세요."
            )
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        request = self.context["request"]
        user = request.user
        if ChatRoom.objects.filter(owner=user).count() >= ChatRoom.MAX_ROOMS_PER_USER:
            raise serializers.ValidationError(
                f"채팅방은 사용자당 최대 {ChatRoom.MAX_ROOMS_PER_USER}개까지만 생성할 수 있습니다."
            )
        is_private = attrs.get("is_private", False)
        password = attrs.get("password", "").strip()
        if is_private and not password:
            raise serializers.ValidationError({"password": "비공개 채팅방은 비밀번호가 필요합니다."})
        if not is_private:
            attrs["password"] = ""
        else:
            attrs["password"] = password
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password", "")
        request = self.context["request"]
        room = ChatRoom.objects.create(owner=request.user, **validated_data)
        if password:
            room.set_password(password)
            room.save(update_fields=["password"])
        return room


class ChatRoomJoinSerializer(serializers.Serializer):
    name = serializers.CharField()
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    def validate(self, attrs):
        request = self.context["request"]
        user = request.user
        name = attrs.get("name", "").strip()
        if not name:
            raise serializers.ValidationError({"name": "채팅방 이름을 입력해 주세요."})
        try:
            room = ChatRoom.objects.get(name=name)
        except ChatRoom.DoesNotExist:
            raise serializers.ValidationError({"name": "해당 이름의 채팅방이 없습니다."})

        is_member = room.memberships.filter(user=user).exists()
        if room.is_private and not is_member:
            password = attrs.get("password", "")
            if not password:
                raise serializers.ValidationError({"password": "비공개 채팅방 비밀번호를 입력해 주세요."})
            if not room.check_password(password):
                raise serializers.ValidationError({"password": "비밀번호가 일치하지 않습니다."})
        if not is_member and room.memberships.count() >= room.capacity:
            raise serializers.ValidationError({"name": "채팅방 정원이 가득 찼습니다."})

        attrs["room"] = room
        attrs["is_member"] = is_member
        return attrs


class ChatMessageSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()
    room = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = ChatMessage
        fields = ["id", "room", "content", "created_at", "is_anonymous", "display_name"]
        read_only_fields = ["id", "room", "created_at", "display_name"]

    def validate_content(self, value):
        text = (value or "").strip()
        if not text:
            raise serializers.ValidationError("내용을 입력해 주세요.")
        if len(text) > 500:
            raise serializers.ValidationError("메시지는 500자 이내로 입력해 주세요.")
        return text

    def create(self, validated_data):
        request = self.context["request"]
        room = self.context["room"]
        return ChatMessage.objects.create(user=request.user, room=room, **validated_data)

    def get_display_name(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if obj.is_anonymous and user and (user.is_staff or user.is_superuser):
            return f"익명({obj.user.username})"
        return obj.display_name

    def validate(self, attrs):
        attrs = super().validate(attrs)
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and (user.is_staff or user.is_superuser):
            attrs["is_anonymous"] = False
        return attrs
