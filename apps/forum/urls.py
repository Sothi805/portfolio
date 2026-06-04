# Web (MVT) URLs
from django.urls import path
from .views import (
    ForumCategoryListView, ForumThreadListView, ForumThreadDetailView,
    ForumCreateThreadView, LeaderboardView, UpvoteReplyView
)

urlpatterns = [
    path('', ForumCategoryListView.as_view(), name='forum_categories'),
    path('leaderboard/', LeaderboardView.as_view(), name='forum_leaderboard'),
    path('<slug:category_slug>/', ForumThreadListView.as_view(), name='forum_thread_list'),
    path('<slug:category_slug>/new/', ForumCreateThreadView.as_view(), name='forum_create_thread'),
    path('<slug:category_slug>/<slug:thread_slug>/', ForumThreadDetailView.as_view(), name='forum_thread_detail'),
    path('reply/<int:reply_id>/upvote/', UpvoteReplyView.as_view(), name='upvote_reply'),
]
