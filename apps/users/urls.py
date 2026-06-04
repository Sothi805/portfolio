# API URLs
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import LoginAPIView, RegisterAPIView, MeAPIView

app_name = 'api_users'

urlpatterns = [
    path('login/', LoginAPIView.as_view(), name='api_login'),
    path('register/', RegisterAPIView.as_view(), name='api_register'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', MeAPIView.as_view(), name='api_me'),
]
