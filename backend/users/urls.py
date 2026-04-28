from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CaptchaView,
    CsrfCookieView,
    LoginView,
    LogoutView,
    PropertyViewSet,
    RegisterView,
    UserViewSet,
)

router = DefaultRouter()
router.register(r'accounts', UserViewSet, basename='user-account')
router.register(r'properties', PropertyViewSet, basename='property')

urlpatterns = [
    path('csrf/', CsrfCookieView.as_view()),
    path('captcha/', CaptchaView.as_view()),
    path('login/', LoginView.as_view()),
    path('logout/', LogoutView.as_view()),
    path('register/', RegisterView.as_view()),
    path('', include(router.urls)),
]
