from django.contrib import admin
from .models import ForumCategory, ForumThread, ForumReply, FlaggedContent, UserBadge, UserPoints


@admin.register(ForumCategory)
class ForumCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(ForumThread)
class ForumThreadAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'category', 'upvotes', 'views_count', 'is_pinned', 'created_at']
    list_filter = ['category', 'is_pinned']
    search_fields = ['title', 'user__username']


@admin.register(ForumReply)
class ForumReplyAdmin(admin.ModelAdmin):
    list_display = ['user', 'thread', 'upvotes', 'is_marked_helpful', 'created_at']


@admin.register(FlaggedContent)
class FlaggedContentAdmin(admin.ModelAdmin):
    list_display = ['content_type', 'content_id', 'reason', 'status', 'confidence_score', 'created_at']
    list_filter = ['status', 'reason', 'content_type']


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ['user', 'badge_type', 'earned_at']


@admin.register(UserPoints)
class UserPointsAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_points', 'updated_at']
    ordering = ['-total_points']
