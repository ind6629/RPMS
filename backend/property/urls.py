from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ComplaintViewSet, RepairOrderViewSet, ServiceFeedbackViewSet

router = DefaultRouter()
router.register(r'repairs', RepairOrderViewSet, basename='repair')
router.register(r'complaints', ComplaintViewSet, basename='complaint')
router.register(r'feedback', ServiceFeedbackViewSet, basename='feedback')

urlpatterns = [
    path('', include(router.urls)),
]
