from django.urls import path

from app.portfolio.views import PortfolioGenerateAPIView

urlpatterns = [
    path("generate", PortfolioGenerateAPIView.as_view(), name="portfolio-generate"),
]