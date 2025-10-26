from django.conf import settings
from django.db import transaction
from django.shortcuts import render
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from app.core.views import CustomPageNumberPagination
from app.global_constants import ErrorMessage, SuccessMessage
from app.job_source.job_source_utils import get_job_alerts_for_user
from app.job_source.models import Source, UserSource
from app.job_source.serializers import SourceCreateSerializer, SourceDisplaySerializer, SourceUpdateSerializer, \
    SourceListFilterDisplaySerializer, SourceListSerializer, UserSourceSelectSerializer, \
    UserSourceSelectDisplaySerializer
from app.portfolio.portfolio_utils import extract_resume_text, get_file_type
from app.utils import get_response_schema
from permissions import IsSuperAdmin, IsUser


# Create your views here.
class SourceCreateAPIView(GenericAPIView):
    permission_classes = [IsSuperAdmin]

    @swagger_auto_schema(
        request_body=
        openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Source name"),
                "api_url": openapi.Schema(type=openapi.TYPE_STRING, description="Source url"),
                "rss_url": openapi.Schema(type=openapi.TYPE_STRING, description="RSS url"),

            },
        )
    )
    def post(self, request):

        if "name" not in request.data or "api_url" not in request.data or "rss_url" not in request.data:
            return get_response_schema(
                {settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [ErrorMessage.MISSING_FIELDS.value]},
                ErrorMessage.BAD_REQUEST.value,
                status.HTTP_400_BAD_REQUEST
            )

        serializer = SourceCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return get_response_schema(serializer.data, SuccessMessage.RECORD_CREATED.value, status.HTTP_201_CREATED)

        return get_response_schema(serializer.errors, ErrorMessage.BAD_REQUEST.value, status.HTTP_400_BAD_REQUEST)


class SourceDetailAPIView(GenericAPIView):
    permission_classes = [IsSuperAdmin]

    def get_object(self, pk):

        source_object = Source.objects.filter(pk=pk, is_active=True)
        if source_object:
            return source_object[0]
        return None

    def get(self, request, pk):

        source = self.get_object(pk)
        if not source:
            return get_response_schema({}, ErrorMessage.NOT_FOUND.value, status.HTTP_404_NOT_FOUND)

        serializer = SourceDisplaySerializer(source)
        return get_response_schema(serializer.data, SuccessMessage.RECORD_RETRIEVED.value, status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=
        openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Source name"),
                "api_url": openapi.Schema(type=openapi.TYPE_STRING, description="Source url"),
                "rss_url": openapi.Schema(type=openapi.TYPE_STRING, description="RSS url"),

            },
        )
    )
    def patch(self, request, pk):

        source = self.get_object(pk)
        if not source:
            return get_response_schema({}, ErrorMessage.NOT_FOUND.value, status.HTTP_404_NOT_FOUND)

        serializer = SourceUpdateSerializer(source, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return get_response_schema(serializer.data, SuccessMessage.RECORD_UPDATED.value, status.HTTP_201_CREATED)

        return get_response_schema(serializer.errors, ErrorMessage.BAD_REQUEST.value, status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):

        source = self.get_object(pk)
        if not source:
            return get_response_schema({}, ErrorMessage.NOT_FOUND.value, status.HTTP_404_NOT_FOUND)

        source.is_active = False
        source.save()
        return get_response_schema({}, SuccessMessage.RECORD_DELETED.value, status.HTTP_204_NO_CONTENT)


class SourceListFilter(ListAPIView):
    """Source: List-filter"""

    serializer_class = SourceListFilterDisplaySerializer
    pagination_class = CustomPageNumberPagination

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsSuperAdmin]

    def get_queryset(self):

        source_queryset = Source.objects.filter(is_active=True).order_by("-updated")

        # Filter by name
        name = self.request.query_params.get("name", None)
        if name:
            source_queryset = source_queryset.filter(name__istartswith=name)

        # Filter by api_url
        api_url = self.request.query_params.get("api_url", None)
        if api_url:
            source_queryset = source_queryset.filter(api_url__icontains=api_url)

        # Filter by rss_url
        rss_url = self.request.query_params.get("rss_url", None)
        if rss_url:
            source_queryset = source_queryset.filter(rss_url__icontains=rss_url)

        return source_queryset

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter("name", openapi.IN_QUERY, description="Filter by name", type=openapi.TYPE_STRING),
            openapi.Parameter("api_url", openapi.IN_QUERY, description="Filter by api_url", type=openapi.TYPE_STRING),
            openapi.Parameter("rss_url", openapi.IN_QUERY, description="Filter by rss_url", type=openapi.TYPE_STRING),

        ]
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class SourceListAPIView(GenericAPIView):
    """Source: List"""
    permission_classes = [IsUser]

    def get(self, request):
        source_queryset = Source.objects.filter(is_active=True).order_by("-updated")
        serializer = SourceListSerializer(source_queryset, many=True)
        return get_response_schema(serializer.data, SuccessMessage.RECORD_RETRIEVED.value, status.HTTP_200_OK)


class SourceSelectAPIView(GenericAPIView):
    """Source: Select"""
    permission_classes = [IsUser]

    source_item_schema = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['source', 'freq', 'alert'],
        properties={
            'source': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the job source'),
            'frequency': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='Frequency of alerts',
                enum=['Once', 'Daily', 'Weekly', 'Monthly']
            ),
            'alert': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Enable or disable alert')
        }
    )

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=source_item_schema,
            description='List of user source preferences'
        )
    )
    def post(self, request):

        with transaction.atomic():
            for source in request.data:
                source["user"] = request.user.id
                serializer = UserSourceSelectSerializer(data=source)
                if serializer.is_valid():
                    serializer.save()
                else:
                    transaction.set_rollback(True)
                    return get_response_schema(serializer.errors, ErrorMessage.BAD_REQUEST.value,
                                               status.HTTP_400_BAD_REQUEST)

        return get_response_schema({}, SuccessMessage.RECORD_CREATED.value, status.HTTP_201_CREATED)


class UserSourceSelectAPIView(GenericAPIView):
    """User Source: Select"""
    permission_classes = [IsUser]

    def get(self, request):
        user_source_queryset = request.user.job_sources.filter(is_active=True).order_by("-updated")
        serializer = UserSourceSelectDisplaySerializer(user_source_queryset, many=True)
        return get_response_schema(serializer.data, SuccessMessage.RECORD_RETRIEVED.value, status.HTTP_200_OK)


class UserSourceUpdateAPIView(GenericAPIView):
    """User Source: Update"""
    permission_classes = [IsUser]

    source_item_schema = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['source', 'freq', 'alert'],
        properties={
            'source': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the job source'),
            'frequency': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='Frequency of alerts',
                enum=['Once', 'Daily', 'Weekly', 'Monthly']
            ),
            'alert': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Enable or disable alert')
        }
    )

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=source_item_schema,
            description='List of user source preferences'
        )
    )
    def post(self, request):

        with transaction.atomic():

            # delete existing user source
            UserSource.objects.filter(user_id=request.user.id).delete()

            for source in request.data:
                source["user"] = request.user.id
                serializer = UserSourceSelectSerializer(data=source)
                if serializer.is_valid():
                    serializer.save()
                else:
                    transaction.set_rollback(True)
                    return get_response_schema(serializer.errors, ErrorMessage.BAD_REQUEST.value,
                                               status.HTTP_400_BAD_REQUEST)

        return get_response_schema({}, SuccessMessage.RECORD_CREATED.value, status.HTTP_201_CREATED)


class GetJobAlertsAPIView(GenericAPIView):
    """Get Job Alerts"""
    permission_classes = [IsUser]

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

        resume_text = extract_resume_text(file_path, file_type)

        job_alerts = get_job_alerts_for_user(resume_text, request.user)
        return get_response_schema(job_alerts, SuccessMessage.RECORD_RETRIEVED.value, status.HTTP_200_OK)

