from django.contrib import admin
from .models import ModerationAction


@admin.register(ModerationAction)
class ModerationActionAdmin(admin.ModelAdmin):
    list_display = ['admin_user', 'action_type', 'target_user', 'created_at']
    list_filter = ['action_type']
    ordering = ['-created_at']
