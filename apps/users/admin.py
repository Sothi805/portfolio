from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'status', 'is_staff', 'created_at']
    list_filter = ['status', 'is_staff', 'is_superuser']
    search_fields = ['username', 'email']
    ordering = ['-created_at']
    fieldsets = UserAdmin.fieldsets + (
        ('Profile', {'fields': ('avatar', 'bio', 'is_admin_user', 'status')}),
    )
