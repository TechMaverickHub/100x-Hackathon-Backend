from django.urls import path

from app.interview.views import GenerateQuestionsAPIView, AnswerQuestionsAPIView

urlpatterns = [
    path("generate-questions", GenerateQuestionsAPIView.as_view(), name="generate-questions"),
    path("answer-questions", AnswerQuestionsAPIView.as_view(), name="answer-questions"),
]