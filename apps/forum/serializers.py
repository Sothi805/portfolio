from rest_framework import serializers
from .models import ForumCategory, ForumThread, ForumReply, UserBadge, UserPoints
from apps.users.serializers import UserSerializer


class ForumCategorySerializer(serializers.ModelSerializer):
    thread_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = ForumCategory
        fields = ['id', 'name', 'slug', 'description', 'icon', 'thread_count']


class ForumReplySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ForumReply
        fields = ['id', 'thread', 'user', 'content', 'upvotes', 'is_marked_helpful', 'created_at']
        read_only_fields = ['id', 'user', 'upvotes', 'created_at']


class ForumThreadSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    replies = ForumReplySerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    reply_count = serializers.SerializerMethodField()

    class Meta:
        model = ForumThread
        fields = [
            'id', 'user', 'category', 'category_name', 'title', 'slug',
            'content', 'views_count', 'upvotes', 'is_pinned',
            'reply_count', 'replies', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'slug', 'views_count', 'upvotes', 'created_at']

    def get_reply_count(self, obj):
        return obj.replies.count()


class UserBadgeSerializer(serializers.ModelSerializer):
    badge_display = serializers.CharField(source='get_badge_type_display', read_only=True)

    class Meta:
        model = UserBadge
        fields = ['id', 'badge_type', 'badge_display', 'earned_at']


class UserPointsSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserPoints
        fields = ['user', 'total_points', 'updated_at']
