import os

from django.conf import settings
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated

from app.global_constants import ErrorMessage, SuccessMessage
from app.portfolio.portfolio_utils import process_resume
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


        file_path = request.user.resume_file.path if hasattr(request.user.resume_file,
                                                             'path') else request.user.resume_file
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        # Determine file type
        if ext == '.pdf':
            file_type = 'pdf'
        elif ext in ['.doc', '.docx']:
            file_type = 'docx'
        else:
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
