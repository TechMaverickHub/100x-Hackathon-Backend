from django.conf import settings
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView

from app.global_constants import ErrorMessage, SuccessMessage
from app.portfolio.portfolio_utils import get_file_type, extract_resume_text
from app.resume.resume_utils import generate_latex_prompt, generate_resume_score, keyword_gap_analysis, \
    auto_rewrite_resume, generate_skill_gap, generate_career_recommendation
from app.utils import get_response_schema
from permissions import IsUser


# Create your views here.
class ResumeGenerateAPIView(GenericAPIView):
    permission_classes = [IsUser]

    resume_request_schema = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=["name", "role", "bio", "email"],
        properties={
            # Home
            "name": openapi.Schema(type=openapi.TYPE_STRING, description="Full name"),
            "role": openapi.Schema(type=openapi.TYPE_STRING, description="Professional title / main expertise"),
            "tagline": openapi.Schema(type=openapi.TYPE_STRING,
                                      description="Short personal tagline or mission statement"),

            # About
            "bio": openapi.Schema(type=openapi.TYPE_STRING, description="2–3 sentence summary about yourself"),
            "skills": openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "technical": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Items(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "skill": openapi.Schema(type=openapi.TYPE_STRING, description="Technical skill name"),
                                "weight": openapi.Schema(type=openapi.TYPE_INTEGER, description="Proficiency 1-5")
                            }
                        ),
                        description="List of technical skills with weights"
                    ),
                    "soft": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Items(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "skill": openapi.Schema(type=openapi.TYPE_STRING, description="Soft skill name"),
                            }
                        ),
                        description="List of soft skills with weights"
                    )
                }
            ),

            # Projects
            "projects": openapi.Schema(
                type=openapi.TYPE_ARRAY,
                description="List of projects with title, description, and link",
                items=openapi.Items(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "title": openapi.Schema(type=openapi.TYPE_STRING, description="Project title"),
                        "desc": openapi.Schema(type=openapi.TYPE_STRING, description="Short description"),
                        "link": openapi.Schema(type=openapi.TYPE_STRING, description="Project URL or repo link",
                                               nullable=True)
                    }
                )
            ),

            # Experience
            "experience": openapi.Schema(
                type=openapi.TYPE_ARRAY,
                description="List of work experience",
                items=openapi.Items(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "role": openapi.Schema(type=openapi.TYPE_STRING, description="Job title"),
                        "company": openapi.Schema(type=openapi.TYPE_STRING, description="Company name"),
                        "duration": openapi.Schema(type=openapi.TYPE_STRING, description="Start-End dates"),
                        "desc": openapi.Schema(type=openapi.TYPE_STRING, description="Responsibilities / achievements")
                    }
                )
            ),

            # Education
            "education": openapi.Schema(
                type=openapi.TYPE_ARRAY,
                description="List of education entries",
                items=openapi.Items(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "degree": openapi.Schema(type=openapi.TYPE_STRING, description="Degree name"),
                        "institution": openapi.Schema(type=openapi.TYPE_STRING, description="Institution name"),
                        "year": openapi.Schema(type=openapi.TYPE_STRING, description="Graduation year")
                    }
                )
            ),

            # Contact
            "email": openapi.Schema(type=openapi.TYPE_STRING, description="Public contact email"),
            "linkedin": openapi.Schema(type=openapi.TYPE_STRING, description="LinkedIn profile link", nullable=True),
            "github": openapi.Schema(type=openapi.TYPE_STRING, description="GitHub profile link", nullable=True),
            "twitter": openapi.Schema(type=openapi.TYPE_STRING, description="Twitter/X profile link", nullable=True)
        },
        example={
            "name": "Abhiroop Bhattacharyya",
            "role": "Software Developer / AI Engineer",
            "tagline": "Building intelligent systems that scale humans.",
            "bio": "Data-driven engineer specializing in Django and GenAI applications.",
            "skills": {
                "technical": [{"skill": "Python", "weight": 5}, {"skill": "Django", "weight": 5}],
                "soft": [{"skill": "Teamwork", "weight": 4}, {"skill": "Leadership", "weight": 4}]
            },
            "projects": [{"title": "CreatorPulse", "desc": "AI newsletter automation platform",
                          "link": "https://github.com/..."}],
            "experience": [{"role": "Software Engineer", "company": "TechCorp", "duration": "2023-2025",
                            "desc": "Built scalable APIs"}],
            "education": [{"degree": "M.Tech CS", "institution": "IIT XYZ", "year": "2023"}],
            "email": "abhiroop@example.com",
            "linkedin": "https://linkedin.com/in/abhiroop",
            "github": "https://github.com/TechMaverickHub",
            "twitter": "https://x.com/abhiroop"
        }
    )

    @swagger_auto_schema(
        operation_description="Generate ATS-friendly LaTeX resume from user input",
        request_body=resume_request_schema,
        responses={200: "Returns LLM prompt for LaTeX resume", 400: "Bad Request"}
    )
    def post(self, request):
        # check if "name", "role", "bio", "email" in request data
        if "name" not in request.data or "role" not in request.data or "bio" not in request.data or "email" not in request.data:
            return get_response_schema({}, ErrorMessage.BAD_REQUEST.value, status.HTTP_400_BAD_REQUEST)

        latex_resume = generate_latex_prompt(request.data)

        return get_response_schema({"resume": latex_resume}, SuccessMessage.RECORD_RETRIEVED.value, status.HTTP_200_OK)


class ResumeScoreAPIView(GenericAPIView):
    permission_classes = [IsUser]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "job_description": openapi.Schema(type=openapi.TYPE_STRING, description="Job description"),
            }
        )
    )
    def post(self, request):

        # check if job_Description is none
        if "job_description" not in request.data:
            return get_response_schema(
                {settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [ErrorMessage.BAD_REQUEST.value]},
                ErrorMessage.BAD_REQUEST.value,
                status.HTTP_400_BAD_REQUEST
            )

        if not request.user.resume_file:
            return get_response_schema(
                {settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [ErrorMessage.RESUME_FILE_MISSING.value]},
                ErrorMessage.BAD_REQUEST.value,
                status.HTTP_400_BAD_REQUEST
            )

        try:
            file_path, file_type = get_file_type(request.user)
        except ValueError:
            return get_response_schema(
                {settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [ErrorMessage.UNSUPPORTED_FILE_TYPE.value]},
                ErrorMessage.BAD_REQUEST.value,
                status.HTTP_400_BAD_REQUEST
            )

        resume_text = extract_resume_text(file_path, file_type)

        result = generate_resume_score(resume_text, request.data.get("job_description"))

        return get_response_schema( result, SuccessMessage.RECORD_RETRIEVED.value, status.HTTP_200_OK)


class ResumeKeywordGapAPIView(GenericAPIView):
    permission_classes = [IsUser]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "job_description": openapi.Schema(type=openapi.TYPE_STRING, description="Job description"),
            }
        )
    )
    def post(self, request):

        # check if job_Description is none
        if "job_description" not in request.data:
            return get_response_schema(
                {settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [ErrorMessage.BAD_REQUEST.value]},
                ErrorMessage.BAD_REQUEST.value,
                status.HTTP_400_BAD_REQUEST
            )

        if not request.user.resume_file:
            return get_response_schema(
                {settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [ErrorMessage.RESUME_FILE_MISSING.value]},
                ErrorMessage.BAD_REQUEST.value,
                status.HTTP_400_BAD_REQUEST
            )

        try:
            file_path, file_type = get_file_type(request.user)
        except ValueError:
            return get_response_schema(
                {settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [ErrorMessage.UNSUPPORTED_FILE_TYPE.value]},
                ErrorMessage.BAD_REQUEST.value,
                status.HTTP_400_BAD_REQUEST
            )

        resume_text = extract_resume_text(file_path, file_type)

        result = keyword_gap_analysis(resume_text, request.data.get("job_description"))

        return get_response_schema( result, SuccessMessage.RECORD_RETRIEVED.value, status.HTTP_200_OK)


class ResumeAutoRewriteAPIView(GenericAPIView):
    permission_classes = [IsUser]

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
        # check if job_Description is none
        if "job_description" not in request.data:
            return get_response_schema(
                {settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [ErrorMessage.BAD_REQUEST.value]},
                ErrorMessage.BAD_REQUEST.value,
                status.HTTP_400_BAD_REQUEST
            )

        if not request.user.resume_file:
            return get_response_schema(
                {settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [ErrorMessage.RESUME_FILE_MISSING.value]},
                ErrorMessage.BAD_REQUEST.value,
                status.HTTP_400_BAD_REQUEST
            )

        try:
            file_path, file_type = get_file_type(request.user)
        except ValueError:
            return get_response_schema(
                {settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [ErrorMessage.UNSUPPORTED_FILE_TYPE.value]},
                ErrorMessage.BAD_REQUEST.value,
                status.HTTP_400_BAD_REQUEST
            )

        resume_text = extract_resume_text(file_path, file_type)

        result = auto_rewrite_resume(resume_text, request.data.get("job_description"), request.data.get("tone", "Professional"))

        return get_response_schema( result, SuccessMessage.RECORD_RETRIEVED.value, status.HTTP_200_OK)

class ResumeSkillsGapAPIView(GenericAPIView):

    permission_classes = [IsUser]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "job_description": openapi.Schema(type=openapi.TYPE_STRING, description="Job description"),
            }
        )
    )
    def post(self, request):

        # check if job_Description is none
        if "job_description" not in request.data:
            return get_response_schema(
                {settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [ErrorMessage.BAD_REQUEST.value]},
                ErrorMessage.BAD_REQUEST.value,
                status.HTTP_400_BAD_REQUEST
            )

        if not request.user.resume_file:
            return get_response_schema(
                {settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [ErrorMessage.RESUME_FILE_MISSING.value]},
                ErrorMessage.BAD_REQUEST.value,
                status.HTTP_400_BAD_REQUEST
            )

        try:
            file_path, file_type = get_file_type(request.user)
        except ValueError:
            return get_response_schema(
                {settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [ErrorMessage.UNSUPPORTED_FILE_TYPE.value]},
                ErrorMessage.BAD_REQUEST.value,
                status.HTTP_400_BAD_REQUEST
            )

        resume_text = extract_resume_text(file_path, file_type)

        result = generate_skill_gap(resume_text, request.data.get("job_description"))

        return get_response_schema(result, SuccessMessage.RECORD_RETRIEVED.value, status.HTTP_200_OK)


class ResumeCareerRecommendationAPIView(GenericAPIView):

    permission_classes = [IsUser]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "job_description": openapi.Schema(type=openapi.TYPE_STRING, description="Job description"),
            }
        )
    )
    def post(self, request):

        # check if job_Description is none
        if "job_description" not in request.data:
            return get_response_schema(
                {settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [ErrorMessage.BAD_REQUEST.value]},
                ErrorMessage.BAD_REQUEST.value,
                status.HTTP_400_BAD_REQUEST
            )

        if not request.user.resume_file:
            return get_response_schema(
                {settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [ErrorMessage.RESUME_FILE_MISSING.value]},
                ErrorMessage.BAD_REQUEST.value,
                status.HTTP_400_BAD_REQUEST
            )

        try:
            file_path, file_type = get_file_type(request.user)
        except ValueError:
            return get_response_schema(
                {settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [ErrorMessage.UNSUPPORTED_FILE_TYPE.value]},
                ErrorMessage.BAD_REQUEST.value,
                status.HTTP_400_BAD_REQUEST
            )

        resume_text = extract_resume_text(file_path, file_type)

        result = generate_career_recommendation(resume_text, request.data.get("job_description"))

        return get_response_schema(result, SuccessMessage.RECORD_RETRIEVED.value, status.HTTP_200_OK)




