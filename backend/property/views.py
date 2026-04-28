import csv
import io

from django.db.models import Count, Q
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from operation.utils import log_action
from users.models import User

from .models import Complaint, RepairOrder, ServiceFeedback
from .serializers import (
    ComplaintCreateSerializer,
    ComplaintSerializer,
    RepairOrderCreateSerializer,
    RepairOrderSerializer,
    ServiceFeedbackCreateSerializer,
    ServiceFeedbackSerializer,
)


def _admin(u):
    return u.is_authenticated and (u.role == 'admin' or getattr(u, 'is_superuser', False))


def _employee(u):
    return u.is_authenticated and u.role == 'employee'


def _owner(u):
    return u.is_authenticated and u.role == 'owner'


def _pick_employee():
    qs = User.objects.filter(role='employee', status=True)
    if not qs.exists():
        return None
    return (
        qs.annotate(
            load=Count(
                'assigned_repairs',
                filter=Q(assigned_repairs__status__in=['pending', 'processing']),
            )
        )
        .order_by('load', 'id')
        .first()
    )


class RepairOrderViewSet(viewsets.ModelViewSet):
    queryset = RepairOrder.objects.all().select_related(
        'property', 'user', 'assigned_to'
    )
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return RepairOrderCreateSerializer
        return RepairOrderSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        u = self.request.user
        if _admin(u):
            st = self.request.query_params.get('status')
            uid = self.request.query_params.get('user')
            eid = self.request.query_params.get('assigned_to')
            pid = self.request.query_params.get('property')
            q = self.request.query_params.get('search')
            if st:
                qs = qs.filter(status=st)
            if uid:
                qs = qs.filter(user_id=uid)
            if eid:
                qs = qs.filter(assigned_to_id=eid)
            if pid:
                qs = qs.filter(property_id=pid)
            if q:
                qs = qs.filter(
                    Q(description__icontains=q)
                    | Q(remark__icontains=q)
                    | Q(user__username__icontains=q)
                    | Q(assigned_to__username__icontains=q)
                    | Q(property__building_number__icontains=q)
                    | Q(property__unit_number__icontains=q)
                    | Q(property__room_number__icontains=q)
                )
            return qs
        if _employee(u):
            st = self.request.query_params.get('status')
            if st:
                qs = qs.filter(status=st)
            return qs.filter(assigned_to=u)
        if _owner(u):
            qs = qs.filter(user=u)
            st = self.request.query_params.get('status')
            if st:
                qs = qs.filter(status=st)
            return qs
        return qs.none()

    def perform_create(self, serializer):
        user = self.request.user
        if _admin(self.request.user):
            uid = self.request.data.get('user')
            owner = User.objects.filter(pk=uid, role='owner').first() if uid else None
            if owner:
                user = owner
        order = serializer.save(user=user, status='pending')
        emp = _pick_employee()
        if emp:
            order.assigned_to = emp
            order.assigned_at = timezone.now()
            order.status = 'processing'
            order.save(update_fields=['assigned_to', 'assigned_at', 'status'])
        log_action(self.request, 'repair_create', f'工单#{order.id}')

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx

    def create(self, request, *args, **kwargs):
        if not (_owner(request.user) or _admin(request.user)):
            return Response({'detail': '仅业主或管理员可创建工单'}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        order = self.get_object()
        if _employee(request.user) and order.assigned_to_id != request.user.id:
            return Response({'detail': '非本人工单'}, status=status.HTTP_403_FORBIDDEN)
        if _owner(request.user):
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        order = self.get_object()
        if _employee(request.user) and order.assigned_to_id != request.user.id:
            return Response({'detail': '非本人工单'}, status=status.HTTP_403_FORBIDDEN)
        if _owner(request.user):
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not _admin(request.user):
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        order = self.get_object()
        if not (_admin(request.user) or (_employee(request.user) and order.assigned_to_id == request.user.id)):
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        order.status = 'completed'
        order.completed_at = timezone.now()
        order.remark = request.data.get('remark', order.remark)
        order.save(update_fields=['status', 'completed_at', 'remark'])
        log_action(request, 'repair_complete', f'工单#{order.id}')
        return Response(RepairOrderSerializer(order).data)

    @action(detail=False, methods=['post'])
    def batch_create(self, request):
        if not _admin(request.user):
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        rows = request.data.get('rows') or []
        if not isinstance(rows, list) or not rows:
            return Response({'detail': 'rows 必须是非空数组'}, status=status.HTTP_400_BAD_REQUEST)
        created = 0
        errors = []
        for idx, row in enumerate(rows, start=1):
            try:
                prop = row.get('property')
                uid = row.get('user')
                if not prop or not uid:
                    errors.append(f'第{idx}行缺少 property 或 user')
                    continue
                user = User.objects.filter(pk=uid, role='owner').first()
                if not user:
                    errors.append(f'第{idx}行业主用户不存在: {uid}')
                    continue
                order = RepairOrder.objects.create(
                    property_id=prop,
                    user=user,
                    description=row.get('description', ''),
                    images=row.get('images') or [],
                    status=row.get('status') or 'pending',
                    assigned_to_id=row.get('assigned_to') or None,
                    remark=row.get('remark', ''),
                )
                if order.status in ('processing', 'completed') and order.assigned_to_id and not order.assigned_at:
                    order.assigned_at = timezone.now()
                    order.save(update_fields=['assigned_at'])
                if order.status == 'completed' and not order.completed_at:
                    order.completed_at = timezone.now()
                    order.save(update_fields=['completed_at'])
                created += 1
            except Exception as exc:
                errors.append(f'第{idx}行失败: {exc}')
        log_action(request, 'repair_batch_create', f'批量创建工单{created}条')
        return Response({'created': created, 'errors': errors})

    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        if not _admin(request.user):
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        qs = RepairOrder.objects.all().select_related('property', 'user', 'assigned_to')
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(['ID', '房产', '报修人', '状态', '指派', '创建时间', '描述'])
        for o in qs:
            w.writerow(
                [
                    o.id,
                    str(o.property),
                    o.user.username,
                    o.get_status_display(),
                    o.assigned_to.username if o.assigned_to else '',
                    o.created_at.strftime('%Y-%m-%d %H:%M'),
                    (o.description or '')[:200],
                ]
            )
        resp = HttpResponse(buf.getvalue(), content_type='text/csv; charset=utf-8-sig')
        resp['Content-Disposition'] = 'attachment; filename="repairs.csv"'
        log_action(request, 'repair_export', '导出工单')
        return resp


class ComplaintViewSet(viewsets.ModelViewSet):
    queryset = Complaint.objects.all().select_related('user', 'handler')
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return ComplaintCreateSerializer
        return ComplaintSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        u = self.request.user
        if _admin(u):
            t = self.request.query_params.get('type')
            st = self.request.query_params.get('status')
            uid = self.request.query_params.get('user')
            q = self.request.query_params.get('search')
            if t:
                qs = qs.filter(type=t)
            if st:
                qs = qs.filter(status=st)
            if uid:
                qs = qs.filter(user_id=uid)
            if q:
                qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
            return qs
        if _owner(u):
            return qs.filter(user=u)
        return qs.none()

    def perform_create(self, serializer):
        user = self.request.user
        if _admin(self.request.user):
            uid = self.request.data.get('user')
            owner = User.objects.filter(pk=uid, role='owner').first() if uid else None
            if owner:
                user = owner
        serializer.save(user=user)
        log_action(self.request, 'complaint_create', '提交投诉建议')

    def create(self, request, *args, **kwargs):
        if not (_owner(request.user) or _admin(request.user)):
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if not _admin(request.user):
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def perform_update(self, serializer):
        inst = serializer.instance
        new_status = serializer.validated_data.get('status', inst.status)
        extra = {}
        if inst.handler_id is None and new_status in ('processing', 'completed'):
            extra['handler'] = self.request.user
        serializer.save(**extra)
        inst = serializer.instance
        if new_status == 'completed' and inst.completed_at is None:
            inst.completed_at = timezone.now()
            inst.save(update_fields=['completed_at'])
        log_action(self.request, 'complaint_update', f'投诉#{inst.id}')

    def destroy(self, request, *args, **kwargs):
        if not _admin(request.user):
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)


class ServiceFeedbackViewSet(viewsets.ModelViewSet):
    queryset = ServiceFeedback.objects.all().select_related('order', 'order__user', 'order__assigned_to')
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return ServiceFeedbackCreateSerializer
        return ServiceFeedbackSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        u = self.request.user
        if _admin(u):
            return qs
        if _owner(u):
            return qs.filter(order__user=u)
        if _employee(u):
            return qs.filter(order__assigned_to=u)
        return qs.none()

    def create(self, request, *args, **kwargs):
        if not _owner(request.user):
            return Response({'detail': '仅业主可提交服务反馈'}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        fb = serializer.save()
        log_action(self.request, 'feedback_create', f'工单#{fb.order_id}')

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx

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
