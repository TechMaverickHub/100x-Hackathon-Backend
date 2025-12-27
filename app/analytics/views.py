from collections import defaultdict
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils.timesince import timesince
from django.utils import timezone
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
            UserSource.objects.select_related("source")
            .filter(is_active=True,source__is_active=True)
            .values("source__name")
            .annotate(user_count=Count("user", distinct=True))
            .order_by("-user_count")
        )

        sources = [item["source__name"] for item in source_stats]
        counts = [item["user_count"] for item in source_stats]

        return_data = {"sources": sources, "counts": counts}

        return get_response_schema(return_data, SuccessMessage.RECORD_RETRIEVED.value, status.HTTP_200_OK)


class DailyAIUsageAPIView(GenericAPIView):
    """
    Returns daily AI call counts grouped by generation type for the super admin dashboard.
    """

    permission_classes = [IsSuperAdmin]

    def get(self, request):
        def parse_date(date_str):
            if not date_str:
                return None
            try:
                return datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return None

        dates_qs = (
            AIAnalytics.objects.filter(is_active=True)
            .annotate(date=TruncDate("created"))
            .values("date")
            .order_by("-date")
            .distinct()
        )[:5]

        # Extract the date objects from the QuerySet
        last_5_dates = [row["date"] for row in dates_qs]

        # --- 2. Filter aggregation to only include the last 5 dates ---
        if not last_5_dates:
            return_data = {"dates": [], "series": [], "total_calls": 0, "totals_by_type": {}}
            return get_response_schema(return_data, SuccessMessage.RECORD_RETRIEVED.value, status.HTTP_200_OK)

        # Filter the main QuerySet by the last 5 dates
        analytics_qs = AIAnalytics.objects.filter(is_active=True, created__date__in=last_5_dates)

        # Aggregate data only for those 5 dates
        aggregated = list(
            analytics_qs
            .annotate(date=TruncDate("created"))
            .values("date", "generation_type")
            .annotate(count=Count("id"))
            .order_by("date", "generation_type")
        )

        date_list = sorted(last_5_dates)
        date_labels = [date.strftime("%Y-%m-%d") for date in date_list]
        date_index = {date: idx for idx, date in enumerate(date_list)}

        series_map = defaultdict(lambda: [0] * len(date_list))
        totals_by_type = defaultdict(int)
        for row in aggregated:
            # Check if the row's date is in the final list, though it should be due to filtering
            if row["date"] in date_index:
                idx = date_index[row["date"]]
                gen_type = row["generation_type"]
                count = row["count"]
                series_map[gen_type][idx] = count
                totals_by_type[gen_type] += count

        totals_by_type = dict(totals_by_type)
        total_calls = sum(totals_by_type.values())
        series = [
            {"label": gen_type, "data": counts}
            for gen_type, counts in series_map.items()
        ]

        return_data = {
            "dates": date_labels,
            "series": series,
            "total_calls": total_calls,
            "totals_by_type": totals_by_type,
        }

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




