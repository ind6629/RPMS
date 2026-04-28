from django.utils import timezone


def log_action(request, action, detail=''):
    from .models import SystemLog

    user = None
    if getattr(request, 'user', None) is not None and request.user.is_authenticated:
        user = request.user
    ip = request.META.get('REMOTE_ADDR')
    if ',' in (ip or ''):
        ip = ip.split(',')[0].strip()
    SystemLog.objects.create(user=user, action=action, detail=detail[:2000], ip_address=ip)
