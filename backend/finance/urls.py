from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BillViewSet, ChargeItemViewSet, PaymentRecordViewSet

router = DefaultRouter()
router.register(r'charge-items', ChargeItemViewSet, basename='charge-item')
router.register(r'bills', BillViewSet, basename='bill')
router.register(r'payments', PaymentRecordViewSet, basename='payment')

urlpatterns = [
    path('', include(router.urls)),
]
