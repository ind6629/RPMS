from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AnnouncementViewSet, DashboardSummaryView, SystemLogViewSet

router = DefaultRouter()
router.register(r'announcements', AnnouncementViewSet, basename='announcement')
router.register(r'logs', SystemLogViewSet, basename='system-log')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/summary/', DashboardSummaryView.as_view()),
]
