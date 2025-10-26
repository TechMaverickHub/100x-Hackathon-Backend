from django.contrib.auth import get_user_model
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils.timesince import timesince
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from app.analytics.models import AIAnalytics
from app.analytics.serializers import AIAnalyticsListFilterDisplaySerializer
from app.core.views import CustomPageNumberPagination
from app.global_constants import RoleConstants, SuccessMessage
from app.job_source.models import Source, UserSource
from app.utils import get_response_schema
from permissions import IsSuperAdmin, IsUser


# Create your views here.
class CountAPIView(GenericAPIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        user_count = get_user_model().objects.filter(is_active=True, role=RoleConstants.USER.value).count()

        last_user_registered = get_user_model().objects.filter(is_active=True, role=RoleConstants.USER.value).order_by(
            '-created').first()
        ime_till_last_user_registered =timesince(last_user_registered.created)

        total_sources = Source.objects.all().count()
        active_sources = Source.objects.filter(is_active=True).count()

        return_data = {
            "user_count": user_count,
            "last_user_registered": last_user_registered.email,
            "time_till_last_user_registered": ime_till_last_user_registered,
            "total_sources": total_sources,
            "active_sources": active_sources
        }

        return get_response_schema(return_data, SuccessMessage.RECORD_RETRIEVED.value, status.HTTP_200_OK)


class UserRegistrationTrendAPIView(GenericAPIView):

    permission_classes = [IsSuperAdmin]

    def get(self, request):
        from django.db.models import Count
        users_by_day = (
            get_user_model().objects
            .filter(is_active=True, role=RoleConstants.USER.value)
            .annotate(date= TruncDate('created'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )

        dates = [u['date'].strftime("%Y-%m-%d") for u in users_by_day]
        counts = [u['count'] for u in users_by_day]

        return_data = {"dates": dates, "counts": counts}

        return get_response_schema(return_data, SuccessMessage.RECORD_RETRIEVED.value, status.HTTP_200_OK)


class SourcePopularityAPIView(GenericAPIView):

    permission_classes = [IsSuperAdmin]

    def get(self, request):
        source_stats = (
            UserSource.objects
            .filter(is_active=True)
            .values("source__name")
            .annotate(user_count=Count("user", distinct=True))
            .order_by("-user_count")
        )

        sources = [item["source__name"] for item in source_stats]
        counts = [item["user_count"] for item in source_stats]

        return_data = {"sources": sources, "counts": counts}

        return get_response_schema(return_data, SuccessMessage.RECORD_RETRIEVED.value, status.HTTP_200_OK)


class CreditRemainingAPIView(GenericAPIView):
    permission_classes = [IsUser]

    def get(self, request):

        credits_used = AIAnalytics.objects.filter(user_id = request.user.id).count()

        credits_remaining = 100 - credits_used

        return_data = {"credits_remaining": credits_remaining}

        return get_response_schema(return_data, SuccessMessage.RECORD_RETRIEVED.value, status.HTTP_200_OK)


class APICallListFilter(ListAPIView):
    serializer_class = AIAnalyticsListFilterDisplaySerializer
    pagination_class = CustomPageNumberPagination

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsUser]

    def get_queryset(self):

        ai_analytics_queryset = AIAnalytics.objects.filter(is_active=True, user_id=self.request.user.id).order_by("-created")

        # Filter by generation_type
        generation_type = self.request.query_params.get("generation_type", None)
        if generation_type:
            ai_analytics_queryset = ai_analytics_queryset.filter(generation_type=generation_type)

        return ai_analytics_queryset

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter("generation_type", openapi.IN_QUERY, description="Filter by name", type=openapi.TYPE_STRING, enum=[choice.value for choice in AIAnalytics.GenerationType])

        ]
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)




