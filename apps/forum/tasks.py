from celery import shared_task


@shared_task
def award_points(user_id, reason, points):
    """Award points to a user and check for badge eligibility"""
    from apps.users.models import CustomUser
    from .models import UserPoints, PointTransaction

    try:
        user = CustomUser.objects.get(id=user_id)
        user_points, _ = UserPoints.objects.get_or_create(user=user)
        user_points.total_points += points
        user_points.save()
        PointTransaction.objects.create(user=user, points=points, reason=reason)
        check_badges.delay(user_id)
    except CustomUser.DoesNotExist:
        pass


@shared_task
def check_badges(user_id):
    """Check and award badges based on user activity"""
    from apps.users.models import CustomUser
    from .models import UserPoints, UserBadge, ForumReply

    try:
        user = CustomUser.objects.get(id=user_id)
        user_points, _ = UserPoints.objects.get_or_create(user=user)

        # New Member - always
        UserBadge.objects.get_or_create(user=user, badge_type='new_member')

        # Active Contributor (100+ points)
        if user_points.total_points >= 100:
            _, created = UserBadge.objects.get_or_create(user=user, badge_type='active_contributor')
            if created:
                notify_badge_earned.delay(user_id, 'Active Contributor')

        # Expert (500+ points)
        if user_points.total_points >= 500:
            _, created = UserBadge.objects.get_or_create(user=user, badge_type='expert')
            if created:
                notify_badge_earned.delay(user_id, 'Expert')

        # Helpful Commenter (20+ replies that got upvotes)
        upvoted = ForumReply.objects.filter(user=user, upvotes__gte=1).count()
        if upvoted >= 20:
            _, created = UserBadge.objects.get_or_create(user=user, badge_type='helpful_commenter')
            if created:
                notify_badge_earned.delay(user_id, 'Helpful Commenter')

    except CustomUser.DoesNotExist:
        pass


@shared_task
def notify_badge_earned(user_id, badge_name):
    """Create in-app notification for badge earned"""
    from apps.users.models import CustomUser
    from apps.notifications.models import Notification

    try:
        user = CustomUser.objects.get(id=user_id)
        Notification.objects.create(
            user=user,
            notification_type='badge',
            title=f'Badge Earned: {badge_name}',
            message=f'Congratulations! You earned the {badge_name} badge!'
        )
    except CustomUser.DoesNotExist:
        pass


@shared_task
def send_email_notification(user_id, subject, message):
    """Send email notification to user"""
    from apps.users.models import CustomUser
    from django.core.mail import send_mail

    try:
        user = CustomUser.objects.get(id=user_id)
        send_mail(subject, message, 'noreply@portfolio.com', [user.email])
    except CustomUser.DoesNotExist:
        pass


@shared_task
def auto_flag_content(content_type, content_id):
    """Automated spam detection"""
    from .models import FlaggedContent, ForumThread, ForumReply

    SPAM_KEYWORDS = ['viagra', 'casino', 'lottery', 'click here', 'free money', 'earn $']

    try:
        if content_type == 'thread':
            obj = ForumThread.objects.get(id=content_id)
            text = f"{obj.title} {obj.content}".lower()
        else:
            obj = ForumReply.objects.get(id=content_id)
            text = obj.content.lower()

        confidence = sum(0.3 for kw in SPAM_KEYWORDS if kw in text)

        if confidence > 0.5:
            FlaggedContent.objects.get_or_create(
                content_type=content_type,
                content_id=content_id,
                defaults={
                    'reason': 'spam',
                    'confidence_score': min(confidence, 1.0)
                }
            )
    except Exception:
        pass
