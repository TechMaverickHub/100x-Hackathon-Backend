from django.urls import path

from app.analytics.views import CountAPIView, UserRegistrationTrendAPIView, \
    SourcePopularityAPIView, CreditRemainingAPIView, APICallListFilter

urlpatterns = [
    path("count", CountAPIView.as_view(), name="count"),
    path("user-registration-trend", UserRegistrationTrendAPIView.as_view(), name="user-registration-trend"),

    path("source-popularity", SourcePopularityAPIView.as_view(), name="source-popularity"),

    path("credit-remaining", CreditRemainingAPIView.as_view(), name="credit-remaining"),

    path("api-call-list-filter", APICallListFilter.as_view(), name="api-call-list-filter"),
]
