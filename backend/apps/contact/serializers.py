from rest_framework import serializers
from .models import UserMessage


class UserMessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserMessage
        fields = [
            'id',
            'subject',
            'body',
            'is_from_admin',
            'admin_reply',
            'replied_at',
            'created_at',
        ]
        read_only_fields = ['id', 'is_from_admin', 'admin_reply', 'replied_at', 'created_at']


class UserMessageOwnSerializer(serializers.ModelSerializer):
    """What a customer sees in the support chat: own message + admin reply."""
    class Meta:
        model = UserMessage
        fields = [
            'id',
            'subject',
            'body',
            'is_from_admin',
            'admin_reply',
            'replied_at',
            'created_at',
        ]
        read_only_fields = fields


class AdminReplyCreateSerializer(serializers.Serializer):
    body = serializers.CharField(trim_whitespace=True)


class UserMessageAdminSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = UserMessage
        fields = [
            'id', 'user_email', 'user_username',
            'subject', 'body',
            'is_from_admin', 'is_read', 'admin_reply', 'replied_at',
            'created_at',
        ]
        read_only_fields = [
            'id', 'user_email', 'user_username',
            'subject', 'body', 'is_from_admin', 'created_at', 'replied_at',
        ]
