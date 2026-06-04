def unread_notifications(request):
    """Inject unread notification count into every template context"""
    count = 0
    if request.user.is_authenticated:
        try:
            from apps.notifications.models import Notification
            count = Notification.objects.filter(user=request.user, read=False).count()
        except Exception:
            pass
    return {'unread_count': count}
