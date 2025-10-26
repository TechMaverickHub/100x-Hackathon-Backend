from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _


# Create your models here.

class AIAnalytics(models.Model):
    # Feature enum declarations
    class GenerationType(models.TextChoices):
        COVER_LETTER = "Cover Letter", _("Cover Letter")

        INTERVIEW_QUESTIONS = "Interview Questions", _("Interview Questions")
        INTERVIEW_ANSWERS = "Interview Answers", _("Interview Answers")

        PORTFOLIO_FROM_RESUME = "Portfolio From Resume", _("Portfolio From Resume")
        PORTFOLIO_FROM_QNA = "Portfolio From QNA", _("Portfolio From QNA")

        RESUME = "Resume", _("Resume")
        RESUME_SCORE = "Resume Score", _("Resume Score")
        RESUME_KEYWORD_GAP = "Resume Keyword Gap", _("Resume Keyword Gap")
        RESUME_AUTO_REWRITE = "Resume Auto Rewrite", _("Resume Auto Rewrite")
        RESUME_SKILLS_GAP = "Resume Skills Gap", _("Resume Skills Gap")
        RESUME_CAREER_RECOMMENDATION = "Resume Career Recommendation", _("Resume Career Recommendation")

    # Foreign key
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="user_ai_analytics",
        related_query_name="user_ai_analytic"
    )

    # Field declarations
    generation_type = models.CharField(
        max_length=50,
        choices=GenerationType.choices,
        default=GenerationType.COVER_LETTER,
    )

    content = models.TextField()

    # Additional Field declarations
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
