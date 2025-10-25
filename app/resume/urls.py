from django.urls import path

from app.resume.views import ResumeGenerateAPIView

urlpatterns = [
    path("generate", ResumeGenerateAPIView.as_view(), name="resume-generate"),
]