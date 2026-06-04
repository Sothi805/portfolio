from django.db import models
from django.conf import settings


class ForumCategory(models.Model):
    """Forum discussion category"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='forum')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Forum Categories'

    def __str__(self):
        return self.name


class ForumThread(models.Model):
    """Forum discussion thread"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='forum_threads')
    category = models.ForeignKey(ForumCategory, on_delete=models.CASCADE, related_name='threads')
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=300, blank=True)
    content = models.TextField()
    views_count = models.IntegerField(default=0)
    upvotes = models.IntegerField(default=0)
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']
        unique_together = ['category', 'slug']

    def __str__(self):
        return self.title

    def reply_count(self):
        return self.replies.count()


class ForumReply(models.Model):
    """Reply to a forum thread"""
    thread = models.ForeignKey(ForumThread, on_delete=models.CASCADE, related_name='replies')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='forum_replies')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='child_replies')
    content = models.TextField()
    upvotes = models.IntegerField(default=0)
    is_marked_helpful = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_marked_helpful', 'created_at']

    def __str__(self):
        return f"Reply by {self.user.username} on {self.thread.title}"


class UpvoteVote(models.Model):
    """Track upvotes for threads/replies"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content_type = models.CharField(max_length=10, choices=[('thread', 'Thread'), ('reply', 'Reply')])
    content_id = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'content_type', 'content_id']


class FlaggedContent(models.Model):
    """Flagged forum content for moderation"""
    content_type = models.CharField(max_length=10, choices=[('thread', 'Thread'), ('reply', 'Reply')])
    content_id = models.IntegerField()
    reason = models.CharField(max_length=20, choices=[
        ('spam', 'Spam'),
        ('harassment', 'Harassment'),
        ('inappropriate', 'Inappropriate Content'),
        ('scam', 'Scam'),
        ('other', 'Other'),
    ])
    confidence_score = models.FloatField(default=0.0)
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('deleted', 'Deleted'),
        ('warned', 'Warned'),
    ], default='pending')
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']


class UserBadge(models.Model):
    """Badge earned by a user"""
    BADGE_TYPES = [
        ('new_member', 'New Member'),
        ('active_contributor', 'Active Contributor'),
        ('expert', 'Expert'),
        ('helpful_commenter', 'Helpful Commenter'),
        ('feedback_hero', 'Feedback Hero'),
        ('job_seeker', 'Job Seeker'),
        ('mentor', 'Mentor'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='badges')
    badge_type = models.CharField(max_length=30, choices=BADGE_TYPES)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'badge_type']

    def __str__(self):
        return f"{self.user.username} - {self.get_badge_type_display()}"

    BADGE_ICONS = {
        'new_member': 'person',
        'active_contributor': 'emoji_events',
        'expert': 'stars',
        'helpful_commenter': 'thumb_up',
        'feedback_hero': 'campaign',
        'job_seeker': 'work',
        'mentor': 'school',
    }

    def get_icon(self):
        return self.BADGE_ICONS.get(self.badge_type, 'badge')


class UserPoints(models.Model):
    """User forum reputation points"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='forum_points')
    total_points = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}: {self.total_points} pts"


class PointTransaction(models.Model):
    """Track individual point events"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='point_transactions')
    points = models.IntegerField()
    reason = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
