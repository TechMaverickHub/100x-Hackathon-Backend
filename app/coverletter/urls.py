from django.urls import path

from app.coverletter.views import CoverletterAPIView

urlpatterns = [
    path("generate", CoverletterAPIView.as_view(), name="resume-generate"),
]