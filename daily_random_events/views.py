import random

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Activity, ActivityLog, GenerationRequest, Suggestion
from .serializers import (
    ActivityLogCreateSerializer,
    ActivityLogSerializer,
    ActivitySerializer,
    GenerateInputSerializer,
    LoginSerializer,
    RegisterSerializer,
    SuggestionSerializer,
    UserSummarySerializer,
)

User = get_user_model()


LEGACY_MOOD_LEVELS = {
    "relaxed": GenerationRequest.Mood.LOW,
    "low_effort": GenerationRequest.Mood.LOW,
    "creative": GenerationRequest.Mood.MEDIUM,
    "social": GenerationRequest.Mood.MEDIUM,
    "energetic": GenerationRequest.Mood.HIGH,
}

TOP_CANDIDATE_WINDOW = 5
FALLBACK_NOTICE = "Nothing fits perfectly. We relaxed one preference."


def _allowed_social_types(preference):
    if preference == GenerationRequest.SocialPreference.SOLO:
        return [Activity.SocialType.SOLO, Activity.SocialType.EITHER]
    if preference == GenerationRequest.SocialPreference.FRIENDS:
        return [Activity.SocialType.FRIENDS, Activity.SocialType.EITHER]
    return list(Activity.SocialType.values)


def _normalize_mood_level(value):
    token = str(value or "").strip().lower()

    if token in GenerationRequest.Mood.values:
        return token

    return LEGACY_MOOD_LEVELS.get(token, token)


def _hard_constraint_activities(
    payload,
    exclude_ids=None,
    *,
    ignore_excluded_categories=False,
):
    exclude_ids = exclude_ids or []

    queryset = Activity.objects.filter(
        is_active=True,
        min_time_minutes__lte=payload["time_minutes"],
        max_budget__lte=payload["budget"],
    )

    if payload.get("excluded_categories") and not ignore_excluded_categories:
        queryset = queryset.exclude(category__in=payload["excluded_categories"])

    if exclude_ids:
        queryset = queryset.exclude(id__in=exclude_ids)

    return list(queryset)


def _activity_matches_mood(activity, mood_token):
    tags = [_normalize_mood_level(tag) for tag in activity.mood_tags]
    return not tags or mood_token in tags


def _activity_matches_social(activity, preference):
    if preference == GenerationRequest.SocialPreference.EITHER:
        return True

    return activity.social_type in _allowed_social_types(preference)


def _rank_candidate_activities(payload, exclude_ids=None):
    hard_candidates = _hard_constraint_activities(payload, exclude_ids=exclude_ids)
    fallback_applied = False

    if not hard_candidates and payload.get("excluded_categories"):
        hard_candidates = _hard_constraint_activities(
            payload,
            exclude_ids=exclude_ids,
            ignore_excluded_categories=True,
        )
        fallback_applied = bool(hard_candidates)

    if not hard_candidates:
        return [], False

    mood_token = _normalize_mood_level(payload["mood"])
    social_preference = payload["social_preference"]
    target_budget = float(payload["budget"]) / 2 if payload["budget"] else 0
    scored = []

    for activity in hard_candidates:
        mood_match = _activity_matches_mood(activity, mood_token)
        social_match = _activity_matches_social(activity, social_preference)
        score = (2 if mood_match else 0) + (1 if social_match else 0)
        budget_distance = abs(float(activity.max_budget) - target_budget)
        scored.append(
            {
                "activity": activity,
                "score": score,
                "budget_distance": budget_distance,
            }
        )

    ranked = sorted(
        scored,
        key=lambda item: (
            -item["score"],
            item["budget_distance"],
            item["activity"].min_time_minutes,
            item["activity"].id,
        ),
    )

    return [item["activity"] for item in ranked], fallback_applied


def _choose_activity(payload, exclude_ids=None):
    ranked_candidates, fallback_applied = _rank_candidate_activities(
        payload,
        exclude_ids=exclude_ids,
    )
    if not ranked_candidates:
        return None, False

    window_size = min(TOP_CANDIDATE_WINDOW, len(ranked_candidates))
    return random.choice(ranked_candidates[:window_size]), fallback_applied


def _serialize_suggestion_response(suggestion, *, fallback_applied=False):
    data = SuggestionSerializer(suggestion).data
    data["fallback_applied"] = fallback_applied
    data["fallback_message"] = FALLBACK_NOTICE if fallback_applied else ""
    return data


def _pending_activity_log_for_user(user):
    return (
        ActivityLog.objects.filter(
            user=user,
            status=ActivityLog.Status.ACCEPTED,
        )
        .select_related("suggestion__activity")
        .order_by("-created_at")
        .first()
    )


class ActivityLogPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50


class RegisterView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {
                "token": token.key,
                "user": UserSummarySerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {
                "token": token.key,
                "user": UserSummarySerializer(user).data,
            }
        )


class MetadataView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        categories = list(
            Activity.objects.filter(is_active=True)
            .order_by("category")
            .values_list("category", flat=True)
            .distinct()
        )
        return Response(
            {
                "categories": categories,
                "moods": list(GenerationRequest.Mood.values),
                "social_preferences": list(GenerationRequest.SocialPreference.values),
            }
        )


class GenerateView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = GenerateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        selected_activity, fallback_applied = _choose_activity(payload)
        if not selected_activity:
            return Response(
                {"detail": "Nothing fits your time and budget right now."},
                status=status.HTTP_404_NOT_FOUND,
            )

        generation_request = GenerationRequest.objects.create(
            user=request.user,
            **payload,
        )
        suggestion = Suggestion.objects.create(
            request=generation_request,
            activity=selected_activity,
            rank_no=1,
        )
        return Response(
            _serialize_suggestion_response(
                suggestion,
                fallback_applied=fallback_applied,
            ),
            status=status.HTTP_201_CREATED,
        )


class RerollView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, request_id):
        generation_request = get_object_or_404(
            GenerationRequest.objects.prefetch_related("suggestions"),
            id=request_id,
            user=request.user,
        )

        exclude_ids = list(
            generation_request.suggestions.values_list("activity_id", flat=True)
        )
        payload = {
            "time_minutes": generation_request.time_minutes,
            "budget": generation_request.budget,
            "mood": generation_request.mood,
            "social_preference": generation_request.social_preference,
            "excluded_categories": generation_request.excluded_categories,
        }
        selected_activity, fallback_applied = _choose_activity(
            payload,
            exclude_ids=exclude_ids,
        )
        if not selected_activity:
            return Response(
                {"detail": "No additional activities fit your time and budget."},
                status=status.HTTP_404_NOT_FOUND,
            )

        next_rank = generation_request.suggestions.count() + 1
        suggestion = Suggestion.objects.create(
            request=generation_request,
            activity=selected_activity,
            rank_no=next_rank,
        )
        return Response(
            _serialize_suggestion_response(
                suggestion,
                fallback_applied=fallback_applied,
            ),
            status=status.HTTP_201_CREATED,
        )


class AcceptSuggestionView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, suggestion_id):
        suggestion = get_object_or_404(
            Suggestion.objects.select_related("request", "activity"),
            id=suggestion_id,
            request__user=request.user,
        )
        existing_log = getattr(suggestion, "activity_log", None)

        if existing_log and existing_log.status != ActivityLog.Status.ACCEPTED:
            return Response(
                {"detail": "This suggestion has already been finalized."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        current_pending = _pending_activity_log_for_user(request.user)
        if current_pending and current_pending.suggestion_id != suggestion.id:
            if current_pending.suggestion.request_id == suggestion.request_id:
                Suggestion.objects.filter(id=current_pending.suggestion_id).update(
                    is_accepted=False
                )
                current_pending.delete()
            else:
                return Response(
                    {
                        "detail": (
                            "Complete or skip your currently accepted activity "
                            "before accepting another."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        Suggestion.objects.filter(
            request=suggestion.request,
            is_accepted=True,
        ).exclude(id=suggestion.id).update(is_accepted=False)

        if not suggestion.is_accepted:
            suggestion.is_accepted = True
            suggestion.save(update_fields=["is_accepted"])

        ActivityLog.objects.get_or_create(
            user=request.user,
            suggestion=suggestion,
            defaults={"status": ActivityLog.Status.ACCEPTED},
        )

        return Response(SuggestionSerializer(suggestion).data)


class ActivityLogListCreateView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = ActivityLogPagination

    def get(self, request):
        status_filter = request.query_params.get("status")
        pending_log = _pending_activity_log_for_user(request.user)
        queryset = ActivityLog.objects.filter(user=request.user).exclude(
            status=ActivityLog.Status.ACCEPTED
        ).select_related("suggestion__activity")
        if status_filter:
            valid_statuses = {
                ActivityLog.Status.COMPLETED,
                ActivityLog.Status.SKIPPED,
            }
            if status_filter not in valid_statuses:
                return Response(
                    {
                        "status": [
                            "Invalid status filter. Use COMPLETED or SKIPPED."
                        ]
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            queryset = queryset.filter(status=status_filter)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = ActivityLogSerializer(page, many=True)
        response = paginator.get_paginated_response(serializer.data)
        response.data["pending"] = (
            ActivityLogSerializer(pending_log).data if pending_log else None
        )
        return response

    def post(self, request):
        serializer = ActivityLogCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        activity_log = serializer.save()
        output = ActivityLogSerializer(activity_log)
        response_status = (
            status.HTTP_201_CREATED
            if getattr(serializer, "was_created", True)
            else status.HTTP_200_OK
        )
        return Response(output.data, status=response_status)


class ActivityLogDetailView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, log_id):
        activity_log = get_object_or_404(
            ActivityLog.objects.select_related("suggestion"),
            id=log_id,
            user=request.user,
        )

        if activity_log.suggestion.is_accepted:
            activity_log.suggestion.is_accepted = False
            activity_log.suggestion.save(update_fields=["is_accepted"])

        activity_log.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminActivityListCreateView(generics.ListCreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAdminUser]
    serializer_class = ActivitySerializer
    queryset = Activity.objects.all().order_by("title")


class AdminActivityDetailView(generics.RetrieveUpdateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAdminUser]
    serializer_class = ActivitySerializer
    queryset = Activity.objects.all()
