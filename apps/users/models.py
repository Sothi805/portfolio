from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """Extended Django User Model"""
    email = models.EmailField(unique=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True, max_length=500)
    is_admin_user = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('suspended', 'Suspended'),
            ('deleted', 'Deleted'),
        ],
        default='active'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.username

    def get_avatar_url(self):
        if self.avatar:
            try:
                return self.avatar.url
            except Exception:
                pass
        return '/static/images/default-avatar.svg'
