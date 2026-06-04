# Web (MVT) URLs
from django.urls import path
from .views import (
    HomeView, PortfolioListView, PortfolioDetailView,
    PortfolioCreateView, PortfolioEditView, PortfolioDashboardView
)

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('portfolios/', PortfolioListView.as_view(), name='portfolio_list'),
    path('portfolios/create/', PortfolioCreateView.as_view(), name='portfolio_create'),
    path('portfolios/dashboard/', PortfolioDashboardView.as_view(), name='portfolio_dashboard'),
    path('portfolios/<slug:portfolio_slug>/', PortfolioDetailView.as_view(), name='portfolio_detail'),
    path('portfolios/<slug:portfolio_slug>/edit/', PortfolioEditView.as_view(), name='portfolio_edit'),
]
