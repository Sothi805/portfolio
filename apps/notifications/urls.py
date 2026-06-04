from django.urls import path
from .views import NotificationListAPIView, MarkReadAPIView

app_name = 'api_notifications'

urlpatterns = [
    path('', NotificationListAPIView.as_view(), name='list'),
    path('mark-read/', MarkReadAPIView.as_view(), name='mark_all_read'),
    path('<int:pk>/read/', MarkReadAPIView.as_view(), name='mark_read'),
]
