from django.urls import path

from .views import (
    ActivityLogDetailView,
    AcceptSuggestionView,
    ActivityLogListCreateView,
    AdminAuditLogListView,
    AdminActivityDetailView,
    AdminActivityCSVImportView,
    AdminActivityListCreateView,
    GenerateView,
    HealthView,
    LoginView,
    MetadataView,
    RegisterView,
    RerollView,
    SavedSuggestionDetailView,
    SavedSuggestionListCreateView,
)

app_name = "daily_random_events"

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("metadata/", MetadataView.as_view(), name="metadata"),
    path("generate/", GenerateView.as_view(), name="generate"),
    path("generate/<int:request_id>/reroll/", RerollView.as_view(), name="reroll"),
    path(
        "suggestions/<int:suggestion_id>/accept/",
        AcceptSuggestionView.as_view(),
        name="accept-suggestion",
    ),
    path("logs/", ActivityLogListCreateView.as_view(), name="activity-logs"),
    path("logs/<int:log_id>/", ActivityLogDetailView.as_view(), name="activity-log-detail"),
    path("saved/", SavedSuggestionListCreateView.as_view(), name="saved-suggestions"),
    path(
        "saved/<int:saved_id>/",
        SavedSuggestionDetailView.as_view(),
        name="saved-suggestion-detail",
    ),
    path(
        "admin/activities/",
        AdminActivityListCreateView.as_view(),
        name="admin-activity-list",
    ),
    path(
        "admin/activities/<int:pk>/",
        AdminActivityDetailView.as_view(),
        name="admin-activity-detail",
    ),
    path(
        "admin/activities/import-csv/",
        AdminActivityCSVImportView.as_view(),
        name="admin-activity-import-csv",
    ),
    path(
        "admin/audit-logs/",
        AdminAuditLogListView.as_view(),
        name="admin-audit-log-list",
    ),
]
