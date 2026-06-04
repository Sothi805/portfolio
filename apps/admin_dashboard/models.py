from django.db import models
from django.conf import settings


class ModerationAction(models.Model):
    """Track admin moderation actions"""
    ACTION_CHOICES = [
        ('delete', 'Delete'),
        ('warn', 'Warn'),
        ('suspend', 'Suspend'),
        ('ban', 'Ban'),
        ('approve', 'Approve'),
    ]

    admin_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='moderation_actions_taken'
    )
    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES)
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='moderation_actions_received', null=True, blank=True
    )
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.admin_user} {self.action_type} on {self.target_user}"
