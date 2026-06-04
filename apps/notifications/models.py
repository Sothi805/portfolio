from django.db import models
from django.conf import settings


class Notification(models.Model):
    """In-app notification for a user"""
    NOTIFICATION_TYPES = [
        ('reply', 'New Reply'),
        ('upvote', 'New Upvote'),
        ('badge', 'Badge Earned'),
        ('flag', 'Content Flagged'),
        ('moderation', 'Moderation Action'),
        ('system', 'System'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    content_id = models.IntegerField(null=True, blank=True)
    title = models.CharField(max_length=200)
    message = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"

    TYPE_ICONS = {
        'reply': 'reply',
        'upvote': 'thumb_up',
        'badge': 'emoji_events',
        'flag': 'flag',
        'moderation': 'gavel',
        'system': 'notifications',
    }

    def get_icon(self):
        return self.TYPE_ICONS.get(self.notification_type, 'notifications')
