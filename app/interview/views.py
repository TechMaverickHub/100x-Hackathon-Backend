from django.conf import settings
from django.shortcuts import render
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView

from app.analytics.analytics_utils import save_ai_analytics
from app.analytics.models import AIAnalytics
from app.global_constants import ErrorMessage, SuccessMessage
from app.interview.interview_utils import generate_interview_questions, generate_interview_score
from app.portfolio.portfolio_utils import get_file_type, extract_resume_text
from app.utils import get_response_schema
from permissions import IsUser


# Create your views here.
class GenerateQuestionsAPIView(GenericAPIView):

    permission_classes = [IsUser]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "job_description": openapi.Schema(type=openapi.TYPE_STRING, description="Job description"),
                "question_type": openapi.Schema(type=openapi.TYPE_STRING, description="Tone of question",
                                       enum=["Technical", "Behavioral", "Mixed"])
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
        question_type = request.data.get("question_type")

        try:
            file_path, file_type = get_file_type(request.user)
        except ValueError:
            return get_response_schema(
                {settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [ErrorMessage.UNSUPPORTED_FILE_TYPE.value]},
                ErrorMessage.BAD_REQUEST.value,
                status.HTTP_400_BAD_REQUEST
            )

        resume_text = extract_resume_text(file_path, file_type)

        question_list = generate_interview_questions(resume_text, job_description, question_type)

        # save to ai analytics
        save_ai_analytics(request.user, AIAnalytics.GenerationType.INTERVIEW_QUESTIONS, question_list)

        return get_response_schema(
            {"questions": question_list},
            SuccessMessage.RECORD_RETRIEVED.value,
            status.HTTP_200_OK
        )

class AnswerQuestionsAPIView(GenericAPIView):
    permission_classes = [IsUser]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "questions": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    description="List of interview questions",
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "text": openapi.Schema(type=openapi.TYPE_STRING, description="Question text"),
                            "type": openapi.Schema(type=openapi.TYPE_STRING, description="Type of question",
                                                   enum=["Technical", "Behavioral", "Mixed"]),
                            "context": openapi.Schema(type=openapi.TYPE_STRING, description="Context for the question"),
                            "answer": openapi.Schema(type=openapi.TYPE_STRING, description="Answer to the question")
                        }
                    )
                ),
                "job_description": openapi.Schema(type=openapi.TYPE_STRING, description="Job description"),

            },
            required=["questions", "job_description"]
        )
    )
    def post (self, request):

        # Check if the user has resume file
        if not request.user.resume_file:
            return get_response_schema(
                {settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [ErrorMessage.RESUME_FILE_MISSING.value]},
                ErrorMessage.BAD_REQUEST.value,
                status.HTTP_400_BAD_REQUEST
            )

        job_description = request.data.get("job_description")
        question_list = request.data.get("questions")

        try:
            file_path, file_type = get_file_type(request.user)
        except ValueError:
            return get_response_schema(
                {settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [ErrorMessage.UNSUPPORTED_FILE_TYPE.value]},
                ErrorMessage.BAD_REQUEST.value,
                status.HTTP_400_BAD_REQUEST
            )

        resume_text = extract_resume_text(file_path, file_type)

        interview_score = generate_interview_score(resume_text, job_description, question_list)

        # save to ai analytics
        save_ai_analytics(request.user, AIAnalytics.GenerationType.INTERVIEW_ANSWERS, interview_score)

        return get_response_schema(
            {"interview_score": interview_score},
            SuccessMessage.RECORD_RETRIEVED.value,
            status.HTTP_200_OK
        )



