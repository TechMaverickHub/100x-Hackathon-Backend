from django.conf import settings
from django.shortcuts import render
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView

from app.analytics.analytics_utils import save_ai_analytics
from app.analytics.models import AIAnalytics
from app.coverletter.coverletter_utils import generate_cover_letter
from app.global_constants import ErrorMessage, SuccessMessage
from app.portfolio.portfolio_utils import get_file_type, extract_resume_text
from app.utils import get_response_schema


# Create your views here.
class CoverletterAPIView(GenericAPIView):

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "job_description": openapi.Schema(type=openapi.TYPE_STRING, description="Job description"),
                "tone": openapi.Schema(type=openapi.TYPE_STRING, description="Tone of the cover letter", enum=["Professional", "Friendly", "Confident", "Creative", "Concise"])
            }
        )
    )
    def post(self, request):
        # Check if the user has resume file
        if not request.user.resume_file:
            return get_response_schema(
                {settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [ErrorMessage.RESUME_FILE_MISSING.value]},
                ErrorMessage.BAD_REQUEST.value,
                status.HTTP_400_BAD_REQUEST
            )

        job_description = request.data.get("job_description")
        tone = request.data.get("tone")

        try:
            file_path, file_type = get_file_type(request.user)
        except ValueError:
            return get_response_schema(
                {settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [ErrorMessage.UNSUPPORTED_FILE_TYPE.value]},
                ErrorMessage.BAD_REQUEST.value,
                status.HTTP_400_BAD_REQUEST
            )

        resume_text = extract_resume_text(file_path, file_type)

        cover_letter = generate_cover_letter(resume_text, job_description, tone)

        # save to ai analytics
        save_ai_analytics(request.user, AIAnalytics.GenerationType.COVER_LETTER, cover_letter)

        return get_response_schema(
            {"cover_letter": cover_letter},
            SuccessMessage.RECORD_RETRIEVED.value,
            status.HTTP_200_OK
        )







