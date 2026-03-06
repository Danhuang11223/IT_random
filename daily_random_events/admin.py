from django.contrib import admin

from .models import (
    Activity,
    ActivityLog,
    AdminAuditLog,
    GenerationRequest,
    Suggestion,
)


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "social_type", "is_active", "is_outdoor")
    list_filter = ("category", "social_type", "is_active", "is_outdoor")
    search_fields = ("title", "description", "category")


@admin.register(GenerationRequest)
class GenerationRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "mood", "social_preference", "created_at")
    list_filter = ("mood", "social_preference", "created_at")
    search_fields = ("user__username",)


@admin.register(Suggestion)
class SuggestionAdmin(admin.ModelAdmin):
    list_display = ("id", "request", "activity", "rank_no", "is_accepted", "created_at")
    list_filter = ("is_accepted", "created_at")
    search_fields = ("activity__title", "request__user__username")


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "rating", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("user__username", "comment", "suggestion__activity__title")


@admin.register(AdminAuditLog)
class AdminAuditLogAdmin(admin.ModelAdmin):
    list_display = ("id", "action", "admin_user", "target", "created_at")
    list_filter = ("action", "created_at")
    search_fields = ("admin_user__username", "target")
