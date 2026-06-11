from rest_framework import serializers
from .models import UserMessage


class UserMessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserMessage
        fields = ['id', 'subject', 'body', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserMessageAdminSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = UserMessage
        fields = [
            'id', 'user_email', 'user_username',
            'subject', 'body',
            'is_read', 'admin_reply', 'replied_at',
            'created_at',
        ]
        read_only_fields = [
            'id', 'user_email', 'user_username',
            'subject', 'body', 'created_at', 'replied_at',
        ]
