# DRF API URLs
from django.urls import path
from .views import ForumCategoryListAPIView, ForumThreadListAPIView, ForumThreadDetailAPIView

urlpatterns = [
    path('categories/', ForumCategoryListAPIView.as_view(), name='api_forum_categories'),
    path('threads/', ForumThreadListAPIView.as_view(), name='api_forum_threads'),
    path('threads/<int:id>/', ForumThreadDetailAPIView.as_view(), name='api_forum_thread_detail'),
]
