# DRF API URLs
from django.urls import path
from .views import PortfolioListAPIView, PortfolioCreateAPIView, PortfolioDetailAPIView

urlpatterns = [
    path('', PortfolioListAPIView.as_view(), name='api_portfolio_list'),
    path('create/', PortfolioCreateAPIView.as_view(), name='api_portfolio_create'),
    path('<slug:slug>/', PortfolioDetailAPIView.as_view(), name='api_portfolio_detail'),
]
