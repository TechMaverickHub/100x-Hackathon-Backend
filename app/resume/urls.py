from django.urls import path

from app.resume.views import ResumeGenerateAPIView, ResumeScoreAPIView, ResumeKeywordGapAPIView, \
    ResumeAutoRewriteAPIView

urlpatterns = [
    path("generate", ResumeGenerateAPIView.as_view(), name="resume-generate"),
    path("score", ResumeScoreAPIView.as_view(), name="resume-score"),
    path("keyword-gap", ResumeKeywordGapAPIView.as_view(), name="resume-keyword-gap"),
    path("auto-rewrite", ResumeAutoRewriteAPIView.as_view(), name="resume-auto-rewrite"),
]