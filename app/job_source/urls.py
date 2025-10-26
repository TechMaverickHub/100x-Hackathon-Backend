from django.urls import path

from app.job_source.views import SourceCreateAPIView, SourceDetailAPIView, SourceListFilter, SourceListAPIView, \
    SourceSelectAPIView, UserSourceSelectAPIView, UserSourceUpdateAPIView

urlpatterns = [

    # Superadmin
    path("", SourceCreateAPIView.as_view(), name="source-create"),
    path("<int:pk>", SourceDetailAPIView.as_view(), name="source-detail"),
    path("list-filter", SourceListFilter.as_view(), name="source-list-filter"),
    path("list", SourceListAPIView.as_view(), name="source-list"),


    # User
    path("select", SourceSelectAPIView.as_view(), name="source-select"),
    path("user-selection", UserSourceSelectAPIView.as_view(), name="user-source-select"),
    path("update-selection", UserSourceUpdateAPIView.as_view(), name="user-source-update"),

]