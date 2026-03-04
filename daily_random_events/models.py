from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F, Q


class Activity(models.Model):
    class SocialType(models.TextChoices):
        SOLO = "SOLO", "Solo"
        FRIENDS = "FRIENDS", "Friends"
        EITHER = "EITHER", "Either"

    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, db_index=True)
    min_time_minutes = models.PositiveIntegerField()
    max_time_minutes = models.PositiveIntegerField()
    min_budget = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    max_budget = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    mood_tags = models.JSONField(default=list, blank=True)
    social_type = models.CharField(
        max_length=20,
        choices=SocialType.choices,
        default=SocialType.EITHER,
        db_index=True,
    )
    is_outdoor = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["category", "is_active"]),
            models.Index(fields=["social_type", "is_active"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(max_time_minutes__gte=F("min_time_minutes")),
                name="activity_time_range_valid",
            ),
            models.CheckConstraint(
                condition=Q(max_budget__gte=F("min_budget")),
                name="activity_budget_range_valid",
            ),
        ]
        ordering = ["title"]

    def __str__(self):
        return self.title


class GenerationRequest(models.Model):
    class Mood(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    class SocialPreference(models.TextChoices):
        SOLO = "SOLO", "Solo"
        FRIENDS = "FRIENDS", "Friends"
        EITHER = "EITHER", "Either"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="generation_requests",
    )
    time_minutes = models.PositiveIntegerField()
    budget = models.DecimalField(max_digits=8, decimal_places=2)
    mood = models.CharField(max_length=20, choices=Mood.choices)
    social_preference = models.CharField(
        max_length=20,
        choices=SocialPreference.choices,
        default=SocialPreference.EITHER,
    )
    excluded_categories = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"Request #{self.pk} by user {self.user_id}"


class Suggestion(models.Model):
    request = models.ForeignKey(
        GenerationRequest,
        on_delete=models.CASCADE,
        related_name="suggestions",
    )
    activity = models.ForeignKey(
        Activity,
        on_delete=models.PROTECT,
        related_name="suggestions",
    )
    rank_no = models.PositiveIntegerField()
    is_accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["rank_no"]
        indexes = [
            models.Index(fields=["request", "rank_no"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["request", "rank_no"],
                name="suggestion_request_rank_unique",
            ),
            models.UniqueConstraint(
                fields=["request"],
                condition=Q(is_accepted=True),
                name="single_accepted_suggestion_per_request",
            ),
        ]

    def __str__(self):
        return f"Suggestion #{self.pk} for request {self.request_id}"


class ActivityLog(models.Model):
    class Status(models.TextChoices):
        ACCEPTED = "ACCEPTED", "Accepted"
        COMPLETED = "COMPLETED", "Completed"
        SKIPPED = "SKIPPED", "Skipped"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="activity_logs",
    )
    suggestion = models.OneToOneField(
        Suggestion,
        on_delete=models.CASCADE,
        related_name="activity_log",
    )
    status = models.CharField(max_length=20, choices=Status.choices)
    rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(rating__isnull=True) | Q(status="COMPLETED"),
                name="rating_requires_completed_status",
            ),
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(status="ACCEPTED"),
                name="single_pending_activity_log_per_user",
            ),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"Log #{self.pk} ({self.status})"
