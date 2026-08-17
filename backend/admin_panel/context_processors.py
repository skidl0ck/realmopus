from core.models import Notification


def notifications(request):
    if not request.user.is_authenticated:
        return {}
    return {
        "unread_notification_count": Notification.objects.filter(recipient=request.user, is_read=False).count(),
    }