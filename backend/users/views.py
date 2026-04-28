import csv
import io
import random

from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.utils.decorators import method_decorator
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from operation.utils import log_action

from .models import Property, User, UserProfile
from .serializers import (
    PasswordChangeSerializer,
    PropertySerializer,
    SelfProfileSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
)


def _is_admin(user):
    return user.is_authenticated and (
        getattr(user, 'role', None) == 'admin' or getattr(user, 'is_superuser', False)
    )


def _is_employee(user):
    return user.is_authenticated and getattr(user, 'role', None) == 'employee'


def _is_owner(user):
    return user.is_authenticated and getattr(user, 'role', None) == 'owner'


class CsrfCookieView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        return Response({'detail': 'ok'})


class CaptchaView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        a = random.randint(1, 9)
        b = random.randint(1, 9)
        request.session['login_captcha_answer'] = str(a + b)
        request.session.modified = True
        return Response({'expression': f'{a} + {b} = ?'})


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().select_related('profile').prefetch_related('properties')
    serializer_class = UserSerializer

    def get_permissions(self):
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ('update', 'partial_update'):
            return UserUpdateSerializer
        return UserSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated:
            return qs.none()
        if _is_admin(user):
            role = self.request.query_params.get('role')
            st = self.request.query_params.get('status')
            q = self.request.query_params.get('search')
            if role:
                qs = qs.filter(role=role)
            if st is not None:
                qs = qs.filter(status=(st.lower() in ('1', 'true', 'yes')))
            if q:
                qs = qs.filter(
                    Q(username__icontains=q) | Q(phone__icontains=q) | Q(email__icontains=q)
                )
            return qs
        return qs.filter(pk=user.pk)

    def create(self, request, *args, **kwargs):
        if not _is_admin(request.user):
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not _is_admin(request.user):
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if not _is_admin(request.user) and str(kwargs.get('pk')) != str(request.user.pk):
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        if not _is_admin(request.user):
            for f in ('status', 'role'):
                request.data.pop(f, None)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if not _is_admin(request.user) and str(kwargs.get('pk')) != str(request.user.pk):
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        if not _is_admin(request.user):
            for f in ('status', 'role'):
                request.data.pop(f, None)
        return super().partial_update(request, *args, **kwargs)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated], url_path='toggle-status')
    def toggle_status(self, request, pk=None):
        if not _is_admin(request.user):
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        u = self.get_object()
        u.status = not u.status
        u.save(update_fields=['status'])
        log_action(request, 'user_toggle_status', f'用户{u.username} status={u.status}')
        return Response(UserSerializer(u).data)

    @action(detail=False, methods=['get'])
    def me(self, request):
        return Response(UserSerializer(request.user).data)

    @action(detail=False, methods=['patch'], permission_classes=[IsAuthenticated])
    def update_profile(self, request):
        ser = SelfProfileSerializer(request.user, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        log_action(request, 'profile_update', '更新个人信息')
        return Response(UserSerializer(request.user).data)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        ser = PasswordChangeSerializer(data=request.data, context={'request': request})
        if ser.is_valid():
            request.user.set_password(ser.validated_data['new_password'])
            request.user.save()
            log_action(request, 'password_change', '修改密码')
            return Response({'message': '密码修改成功'})
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    """不设 SessionAuthentication，避免 DRF 对已带 session 的匿名请求做 CSRF 校验导致 403。"""
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        username = (request.data.get('username') or '').strip()
        password = request.data.get('password') or ''
        selected_role = (request.data.get('role') or '').strip()
        captcha = request.data.get('captcha', '')

        expected = request.session.get('login_captcha_answer')
        if expected is None or str(captcha).strip() != str(expected):
            return Response({'error': '验证码错误或已过期'}, status=status.HTTP_400_BAD_REQUEST)
        request.session.pop('login_captcha_answer', None)

        user = authenticate(request, username=username, password=password)
        if user is None:
            log_action(request, 'login_failed', f'用户{username}')
            return Response({'error': '用户名或密码错误'}, status=status.HTTP_401_UNAUTHORIZED)
        if not user.status:
            return Response({'error': '账号已被禁用'}, status=status.HTTP_401_UNAUTHORIZED)

        if selected_role:
            if selected_role not in ('owner', 'employee', 'admin'):
                return Response({'error': '角色参数不合法'}, status=status.HTTP_400_BAD_REQUEST)
            user_is_admin = user.role == 'admin' or getattr(user, 'is_superuser', False)
            if selected_role == 'admin':
                if not user_is_admin:
                    return Response({'error': '所选角色与账号角色不一致'}, status=status.HTTP_401_UNAUTHORIZED)
            elif user.role != selected_role:
                return Response({'error': '所选角色与账号角色不一致'}, status=status.HTTP_401_UNAUTHORIZED)

        login(request, user)
        log_action(request, 'login', f'用户{user.username}')
        return Response({'user': UserSerializer(user).data, 'role': user.role})


@method_decorator(csrf_exempt, name='dispatch')
class LogoutView(APIView):
    """不用 DRF SessionAuthentication（否则会强制 CSRF）；用户以 Django 中间件 session 为准。"""
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        drq = request._request
        if not drq.user.is_authenticated:
            return Response({'detail': '未登录'}, status=status.HTTP_401_UNAUTHORIZED)
        log_action(drq, 'logout', f'用户{drq.user.username}')
        logout(drq)
        return Response({'message': '登出成功'})


@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        captcha = request.data.get('captcha', '')
        expected = request.session.get('login_captcha_answer')
        if expected is None or str(captcha).strip() != str(expected):
            return Response({'error': '验证码错误或已过期'}, status=status.HTTP_400_BAD_REQUEST)
        request.session.pop('login_captcha_answer', None)

        data = request.data.copy()
        data['role'] = 'owner'
        ser = UserCreateSerializer(data=data)
        if ser.is_valid():
            user = ser.save()
            log_action(request, 'register', f'注册{user.username}')
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


class PropertyViewSet(viewsets.ModelViewSet):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer

    def get_permissions(self):
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated:
            return qs.none()
        if _is_owner(user):
            return qs.filter(owner=user)
        if _is_admin(user) or _is_employee(user):
            ptype = self.request.query_params.get('type')
            building = self.request.query_params.get('building')
            owner = self.request.query_params.get('owner')
            q = self.request.query_params.get('search')
            if ptype:
                qs = qs.filter(property_type=ptype)
            if building:
                qs = qs.filter(Q(parent_id=building) | Q(id=building))
            if owner:
                qs = qs.filter(owner_id=owner)
            if q:
                qs = qs.filter(
                    Q(name__icontains=q)
                    | Q(building_number__icontains=q)
                    | Q(unit_number__icontains=q)
                    | Q(room_number__icontains=q)
                )
            return qs
        return qs.none()

    def create(self, request, *args, **kwargs):
        if not _is_admin(request.user):
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not _is_admin(request.user):
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if not _is_admin(request.user):
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if not _is_admin(request.user):
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        return super().partial_update(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def my_properties(self, request):
        if not _is_owner(request.user):
            return Response({'error': '仅业主可访问'}, status=status.HTTP_403_FORBIDDEN)
        rows = Property.objects.filter(owner=request.user, property_type='room', status=True).order_by(
            'building_number', 'unit_number', 'room_number'
        )
        page = self.paginate_queryset(rows)
        if page is not None:
            ser = PropertySerializer(page, many=True)
            return self.get_paginated_response(ser.data)
        return Response(PropertySerializer(rows, many=True).data)

    @action(detail=False, methods=['get'])
    def tree(self, request):
        if not (_is_admin(request.user) or _is_employee(request.user)):
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        buildings = Property.objects.filter(property_type='building', status=True)
        data = []
        for building in buildings:
            bd = PropertySerializer(building).data
            bd['children'] = []
            units = Property.objects.filter(parent=building, property_type='unit', status=True)
            for unit in units:
                ud = PropertySerializer(unit).data
                ud['children'] = PropertySerializer(
                    Property.objects.filter(parent=unit, property_type='room', status=True),
                    many=True,
                ).data
                bd['children'].append(ud)
            data.append(bd)
        return Response(data)

    @action(detail=False, methods=['post'])
    def bulk_import(self, request):
        if not _is_admin(request.user):
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        rows = request.data.get('rows') or []
        created = 0
        for row in rows:
            bn = str(row.get('building_number', '')).strip()
            un = str(row.get('unit_number', '')).strip()
            rn = str(row.get('room_number', '')).strip()
            area = row.get('area')
            if not bn or not un or not rn:
                continue
            b, _ = Property.objects.get_or_create(
                property_type='building',
                building_number=bn,
                parent=None,
                defaults={'name': f'{bn}栋', 'status': True},
            )
            u, _ = Property.objects.get_or_create(
                property_type='unit',
                building_number=bn,
                unit_number=un,
                parent=b,
                defaults={'name': f'{bn}栋{un}单元', 'status': True},
            )
            Property.objects.get_or_create(
                property_type='room',
                building_number=bn,
                unit_number=un,
                room_number=rn,
                parent=u,
                defaults={
                    'name': f'{bn}-{un}-{rn}',
                    'area': area,
                    'status': True,
                },
            )
            created += 1
        log_action(request, 'property_bulk_import', f'导入{created}条')
        return Response({'created': created})

    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        if not _is_admin(request.user):
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        rooms = Property.objects.filter(property_type='room').select_related('owner', 'parent')
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(
            ['楼栋', '单元', '房号', '面积', '业主用户名', '状态']
        )
        for r in rooms:
            w.writerow(
                [
                    r.building_number,
                    r.unit_number,
                    r.room_number,
                    r.area or '',
                    r.owner.username if r.owner else '',
                    '启用' if r.status else '禁用',
                ]
            )
        resp = HttpResponse(buf.getvalue(), content_type='text/csv; charset=utf-8-sig')
        resp['Content-Disposition'] = 'attachment; filename="properties.csv"'
        log_action(request, 'property_export', '导出房产')
        return resp
