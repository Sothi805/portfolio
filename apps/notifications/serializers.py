from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    icon = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id', 'notification_type', 'content_id', 'title', 'message', 'read', 'icon', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_icon(self, obj):
        return obj.get_icon()
