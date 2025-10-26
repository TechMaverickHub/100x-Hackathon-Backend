import os

from django.conf import settings
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated

from app.global_constants import ErrorMessage, SuccessMessage
from app.portfolio.portfolio_utils import process_resume, generate_portfolio_from_qna, get_file_type
from app.utils import get_response_schema


# Create your views here.
class PortfolioGenerateAPIView(GenericAPIView):
    """ View: Portfolio Generate API View """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Check if the user has resume file
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
        phtml_output = process_resume(file_path, file_type)

        return get_response_schema(
            {"html": phtml_output},
            SuccessMessage.RECORD_RETRIEVED.value,
            status.HTTP_200_OK
        )

class PortfolioGenerateFromQNAAPIView(GenericAPIView):
    """View: Portfolio Generate API View"""

    permission_classes = [IsAuthenticated]

    # Define the OpenAPI request body schema directly
    @swagger_auto_schema(
        operation_description="Generate single-page portfolio HTML from guided Q&A user input",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["name", "role", "bio", "email"],
            properties={
                # Home
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="What's your full name?"),
                "role": openapi.Schema(type=openapi.TYPE_STRING, description="What's your professional title or main expertise?"),
                "tagline": openapi.Schema(type=openapi.TYPE_STRING, description="Short personal tagline or mission statement."),

                # About
                "bio": openapi.Schema(type=openapi.TYPE_STRING, description="Write a 2–3 sentence summary about yourself (for the About section)."),
                "skills": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="List of top technical and soft skills (e.g., ['Python','Django','GenAI'])."
                ),

                # Projects
                "projects": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    description="List of 2–4 key projects. Each should include title, desc, and link.",
                    items=openapi.Items(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "title": openapi.Schema(type=openapi.TYPE_STRING, description="Project title (e.g., 'CreatorPulse')"),
                            "desc": openapi.Schema(type=openapi.TYPE_STRING, description="Short project description (1–2 sentences)"),
                            "link": openapi.Schema(type=openapi.TYPE_STRING, description="Project URL or repo link", nullable=True),
                        }
                    ),
                ),

                # Contact
                "email": openapi.Schema(type=openapi.TYPE_STRING, description="Your public contact email."),
                "linkedin": openapi.Schema(type=openapi.TYPE_STRING, description="LinkedIn profile link.", nullable=True),
                "github": openapi.Schema(type=openapi.TYPE_STRING, description="GitHub profile link.", nullable=True),
                "twitter": openapi.Schema(type=openapi.TYPE_STRING, description="Twitter/X profile link (optional).", nullable=True),
            },
            example={
                "name": "Abhiroop Bhattacharyya",
                "role": "Software Developer",
                "tagline": "Building intelligent systems that scale humans.",
                "bio": "Data-driven engineer specializing in Django and GenAI applications.",
                "skills": ["Python", "Django", "React", "Generative AI"],
                "projects": [
                    {
                        "title": "CreatorPulse",
                        "desc": "AI newsletter automation platform with Django + React.",
                        "link": "https://github.com/TechMaverickHub/100x-LLM-Assignment-CreatorPulse-frontend"
                    }
                ],
                "email": "abhiroop@example.com",
                "linkedin": "https://linkedin.com/in/abhiroop",
                "github": "https://github.com/TechMaverickHub"
            }
        ),
        responses={200: "Generated HTML in response['html']", 400: "Bad Request"},
    )
    def post(self, request):
        qna_data = request.data

        # Basic validation (you can extend this)
        if not qna_data.get("name") or not qna_data.get("role"):
            return get_response_schema(
                {"error": "Missing required fields (name, role)."},
                ErrorMessage.BAD_REQUEST.value,
                status.HTTP_400_BAD_REQUEST,
            )

        # Pass QnA dict to your generator function
        html_output = generate_portfolio_from_qna(qna_data)

        return get_response_schema(
            {"html": html_output},
            SuccessMessage.RECORD_RETRIEVED.value,
            status.HTTP_200_OK,
        )