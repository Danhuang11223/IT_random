from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed

from .models import Activity, ActivityLog, GenerationRequest, Suggestion

User = get_user_model()


class UserSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email")


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    email = serializers.EmailField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ("username", "email", "password")

    def validate_email(self, value):
        return value.lower()

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        request = self.context.get("request")
        user = authenticate(
            request=request,
            username=attrs["username"],
            password=attrs["password"],
        )
        if not user or not user.is_active:
            raise AuthenticationFailed("Invalid username or password.")
        attrs["user"] = user
        return attrs


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = (
            "id",
            "title",
            "description",
            "category",
            "min_time_minutes",
            "max_time_minutes",
            "min_budget",
            "max_budget",
            "mood_tags",
            "social_type",
            "is_outdoor",
            "is_active",
        )
        read_only_fields = ("id",)


class GenerateInputSerializer(serializers.Serializer):
    time_minutes = serializers.IntegerField(min_value=1, max_value=1440)
    budget = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=0)
    mood = serializers.ChoiceField(choices=GenerationRequest.Mood.choices)
    social_preference = serializers.ChoiceField(
        choices=GenerationRequest.SocialPreference.choices,
        default=GenerationRequest.SocialPreference.EITHER,
    )
    excluded_categories = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        default=list,
    )

    def validate_excluded_categories(self, value):
        cleaned = []
        seen = set()
        for item in value:
            normalized = item.strip().upper()
            if normalized and normalized not in seen:
                cleaned.append(normalized)
                seen.add(normalized)
        return cleaned


class SuggestionSerializer(serializers.ModelSerializer):
    activity = ActivitySerializer(read_only=True)
    request_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Suggestion
        fields = (
            "id",
            "request_id",
            "rank_no",
            "is_accepted",
            "created_at",
            "activity",
        )


class ActivityLogCreateSerializer(serializers.ModelSerializer):
    suggestion_id = serializers.PrimaryKeyRelatedField(
        queryset=Suggestion.objects.select_related("request").all(),
        source="suggestion",
        write_only=True,
    )

    class Meta:
        model = ActivityLog
        fields = ("suggestion_id", "status", "rating", "comment")

    def validate(self, attrs):
        request = self.context["request"]
        suggestion = attrs["suggestion"]
        status_value = attrs["status"]
        rating = attrs.get("rating")
        existing_log = getattr(suggestion, "activity_log", None)

        if suggestion.request.user_id != request.user.id:
            raise serializers.ValidationError(
                {"suggestion_id": "You can only log your own suggestions."}
            )

        if status_value == ActivityLog.Status.ACCEPTED:
            raise serializers.ValidationError(
                {"status": "Use the accept action to create a pending history item."}
            )

        if existing_log and existing_log.status != ActivityLog.Status.ACCEPTED:
            raise serializers.ValidationError(
                {"suggestion_id": "This suggestion has already been logged."}
            )

        if not existing_log and not suggestion.is_accepted:
            raise serializers.ValidationError(
                {"suggestion_id": "Accept the suggestion before logging an outcome."}
            )

        if status_value == ActivityLog.Status.SKIPPED and rating is not None:
            raise serializers.ValidationError(
                {"rating": "Rating is only allowed for completed activities."}
            )

        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        suggestion = validated_data["suggestion"]
        existing_log = getattr(suggestion, "activity_log", None)
        status_value = validated_data["status"]

        if status_value == ActivityLog.Status.SKIPPED:
            validated_data["rating"] = None

        if existing_log and existing_log.status == ActivityLog.Status.ACCEPTED:
            existing_log.status = status_value
            existing_log.rating = validated_data.get("rating")
            existing_log.comment = validated_data.get("comment", "")
            existing_log.save(update_fields=["status", "rating", "comment", "updated_at"])
            self.was_created = False
            return existing_log

        self.was_created = True
        return ActivityLog.objects.create(user=request.user, **validated_data)


class ActivityLogSerializer(serializers.ModelSerializer):
    suggestion_id = serializers.IntegerField(read_only=True)
    request_id = serializers.IntegerField(source="suggestion.request_id", read_only=True)
    activity = ActivitySerializer(source="suggestion.activity", read_only=True)

    class Meta:
        model = ActivityLog
        fields = (
            "id",
            "suggestion_id",
            "request_id",
            "status",
            "rating",
            "comment",
            "created_at",
            "updated_at",
            "activity",
        )
