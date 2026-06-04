from django.urls import path
from .views import (
    AdminDashboardIndexView,
    AdminUsersView,
    AdminPortfoliosView,
    AdminModerationView,
    AdminUserDetailView,
    AdminPortfolioDetailView,
    AdminConnectView,
    AdminDisconnectView,
)

urlpatterns = [
    path('', AdminDashboardIndexView.as_view(), name='admin_dashboard'),
    path('users/', AdminUsersView.as_view(), name='admin_users'),
    path('users/<int:pk>/', AdminUserDetailView.as_view(), name='admin_user_detail'),
    path('users/<int:pk>/connect/', AdminConnectView.as_view(), name='admin_connect'),
    path('portfolios/', AdminPortfoliosView.as_view(), name='admin_portfolios'),
    path('portfolios/<int:pk>/', AdminPortfolioDetailView.as_view(), name='admin_portfolio_detail'),
    path('moderation/', AdminModerationView.as_view(), name='admin_moderation'),
    path('disconnect/', AdminDisconnectView.as_view(), name='admin_disconnect'),
]
