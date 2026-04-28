import csv
import io

from django.db.models import Q
from django.db.models import Count, Sum
from django.db.models.functions import ExtractMonth, ExtractYear
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from operation.utils import log_action
from finance.models import Bill, PaymentRecord
from property.models import Complaint, RepairOrder
from users.models import Property, User

from .models import Announcement, SystemLog
from .serializers import AnnouncementSerializer, SystemLogSerializer


def _admin(u):
    return u.is_authenticated and (u.role == 'admin' or getattr(u, 'is_superuser', False))


def _month_key(dt):
    if not dt:
        return None
    if timezone.is_aware(dt):
        dt = timezone.localtime(dt)
    return dt.strftime('%Y-%m')


class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not _admin(request.user):
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)

        rooms_total = Property.objects.filter(property_type='room').count()
        rooms_bound = Property.objects.filter(property_type='room', owner__isnull=False).count()
        repairs_total = RepairOrder.objects.count()
        complaints_total = Complaint.objects.count()

        summary = {
            'users_total': User.objects.count(),
            'owners_total': User.objects.filter(role='owner').count(),
            'employees_total': User.objects.filter(role='employee').count(),
            'admins_total': User.objects.filter(Q(role='admin') | Q(is_superuser=True)).count(),
            'properties_total': Property.objects.count(),
            'rooms_total': rooms_total,
            'rooms_bound': rooms_bound,
            'rooms_unbound': max(rooms_total - rooms_bound, 0),
            'repairs_total': repairs_total,
            'repairs_pending': RepairOrder.objects.filter(status='pending').count(),
            'repairs_processing': RepairOrder.objects.filter(status='processing').count(),
            'repairs_completed': RepairOrder.objects.filter(status='completed').count(),
            'complaints_total': complaints_total,
            'complaints_pending': Complaint.objects.filter(status='pending').count(),
            'complaints_processing': Complaint.objects.filter(status='processing').count(),
            'complaints_completed': Complaint.objects.filter(status='completed').count(),
            'bills_total': Bill.objects.count(),
            'bills_unpaid': Bill.objects.filter(status='unpaid').count(),
            'bills_paid': Bill.objects.filter(status='paid').count(),
            'bills_overdue': Bill.objects.filter(status='overdue').count(),
            'announcements_published': Announcement.objects.filter(is_published=True).count(),
            'logs_total': SystemLog.objects.count(),
        }

        repair_month_map = {}
        for created_at in RepairOrder.objects.values_list('created_at', flat=True):
            key = _month_key(created_at)
            if key:
                repair_month_map[key] = repair_month_map.get(key, 0) + 1

        payment_month_map = {
            row['year_month']: float(row['value'] or 0)
            for row in Bill.objects.values('year_month').annotate(value=Sum('amount')).order_by('year_month')
            if row.get('year_month')
        }

        month_keys = []
        now = timezone.localdate()
        for i in range(5, -1, -1):
            year = now.year
            month = now.month - i
            while month <= 0:
                month += 12
                year -= 1
            month_keys.append(f'{year:04d}-{month:02d}')

        repair_trend = [{'label': k, 'value': repair_month_map.get(k, 0)} for k in month_keys]
        finance_trend = [{'label': k, 'value': payment_month_map.get(k, 0)} for k in month_keys]

        complaint_types = [
            {'label': label, 'value': Complaint.objects.filter(type=key).count()}
            for key, label in Complaint.TYPE_CHOICES
        ]

        employee_rows = (
            User.objects.filter(role='employee')
            .annotate(done_count=Count('assigned_repairs', filter=Q(assigned_repairs__status='completed')))
            .order_by('-done_count', 'id')[:6]
        )
        employee_ranking = [
            {'label': row.username, 'value': row.done_count or 0}
            for row in employee_rows
        ]

        return Response(
            {
                'summary': summary,
                'repair_trend': repair_trend,
                'finance_trend': finance_trend,
                'complaint_types': complaint_types,
                'property_binding': [
                    {'label': '已绑定', 'value': rooms_bound},
                    {'label': '未绑定', 'value': max(rooms_total - rooms_bound, 0)},
                ],
                'employee_ranking': employee_ranking,
            }
        )


class AnnouncementViewSet(viewsets.ModelViewSet):
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if _admin(self.request.user):
            qs = super().get_queryset()
            q = self.request.query_params.get('search')
            t = self.request.query_params.get('type')
            published = self.request.query_params.get('is_published')
            if q:
                qs = qs.filter(Q(title__icontains=q) | Q(content__icontains=q))
            if t:
                qs = qs.filter(type=t)
            if published is not None:
                qs = qs.filter(is_published=(str(published).lower() in ('1', 'true', 'yes')))
            return qs
        return Announcement.objects.none()

    def perform_create(self, serializer):
        obj = serializer.save()
        log_action(self.request, 'announcement_create', f'公告#{obj.id}')

    def create(self, request, *args, **kwargs):
        if not _admin(request.user):
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if not _admin(request.user):
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if not _admin(request.user):
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not _admin(request.user):
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def platform(self, request):
        now = timezone.now()
        qs = (
            Announcement.objects.filter(
                is_published=True,
                is_withdrawn=False,
                is_archived=False,
            )
            .filter(Q(publish_time__isnull=True) | Q(publish_time__lte=now))
            .order_by('-publish_time', '-created_at')
        )
        page = self.paginate_queryset(qs)
        if page is not None:
            ser = AnnouncementSerializer(page, many=True)
            return self.get_paginated_response(ser.data)
        return Response(AnnouncementSerializer(qs, many=True).data)


class SystemLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SystemLog.objects.all().select_related('user')
    serializer_class = SystemLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not _admin(self.request.user):
            return SystemLog.objects.none()
        qs = super().get_queryset()
        act = self.request.query_params.get('action')
        uid = self.request.query_params.get('user')
        if act:
            qs = qs.filter(action__icontains=act)
        if uid:
            qs = qs.filter(user_id=uid)
        return qs

    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        if not _admin(request.user):
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        qs = SystemLog.objects.all().select_related('user')
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(['时间', '用户', '操作', '详情', 'IP'])
        for row in qs[:5000]:
            w.writerow(
                [
                    row.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    row.user.username if row.user else '',
                    row.action,
                    (row.detail or '')[:500],
                    row.ip_address or '',
                ]
            )
        resp = HttpResponse(buf.getvalue(), content_type='text/csv; charset=utf-8-sig')
        resp['Content-Disposition'] = 'attachment; filename="system_logs.csv"'
        log_action(request, 'log_export', '导出系统日志')
        return resp

    @action(detail=False, methods=['post'])
    def manual_add(self, request):
        if not _admin(request.user):
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        action_name = str(request.data.get('action') or '').strip()
        if not action_name:
            return Response({'detail': '缺少 action'}, status=status.HTTP_400_BAD_REQUEST)
        detail = request.data.get('detail', '')
        row = SystemLog.objects.create(
            user=request.user,
            action=action_name[:64],
            detail=detail,
            ip_address=request.META.get('REMOTE_ADDR'),
        )
        return Response(SystemLogSerializer(row).data, status=status.HTTP_201_CREATED)
