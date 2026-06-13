from rest_framework import serializers

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    """A review as shown to everyone reading a product page."""
    author = serializers.CharField(source='user.username', read_only=True)
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ['id', 'author', 'rating', 'body', 'created_at', 'is_mine']
        read_only_fields = fields

    def get_is_mine(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        return bool(user and user.is_authenticated and obj.user_id == user.id)


class ReviewWriteSerializer(serializers.ModelSerializer):
    """Payload a customer sends to leave or update their review."""
    class Meta:
        model = Review
        fields = ['rating', 'body']
        extra_kwargs = {'body': {'required': False, 'allow_blank': True}}
