from django.urls import path

from app.portfolio.views import PortfolioGenerateAPIView, PortfolioGenerateFromQNAAPIView

urlpatterns = [
    path("generate-from-resume", PortfolioGenerateAPIView.as_view(), name="portfolio-generate"),
    path("generate-from-qna", PortfolioGenerateFromQNAAPIView.as_view(), name="portfolio-generate-from-qna"),
]