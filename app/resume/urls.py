from django.urls import path

from app.resume.views import ResumeGenerateAPIView, ResumeScoreAPIView, ResumeKeywordGapAPIView, \
    ResumeAutoRewriteAPIView, ResumeSkillsGapAPIView, ResumeCareerRecommendationAPIView

urlpatterns = [
    path("generate", ResumeGenerateAPIView.as_view(), name="resume-generate"),
    path("score", ResumeScoreAPIView.as_view(), name="resume-score"),
    path("keyword-gap", ResumeKeywordGapAPIView.as_view(), name="resume-keyword-gap"),
    path("auto-rewrite", ResumeAutoRewriteAPIView.as_view(), name="resume-auto-rewrite"),

    path("skills-gap", ResumeSkillsGapAPIView.as_view(), name="resume-skills-gap"),
    path("generate_career-recommendation", ResumeCareerRecommendationAPIView.as_view(), name="resume-career-recommendation"),
]