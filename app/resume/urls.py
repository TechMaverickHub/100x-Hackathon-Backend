from django.urls import path

from app.resume.views import ResumeGenerateAPIView, ResumeScoreAPIView

urlpatterns = [
    path("generate", ResumeGenerateAPIView.as_view(), name="resume-generate"),
    path("score", ResumeScoreAPIView.as_view(), name="resume-score"),
]