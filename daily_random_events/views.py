import random
import csv
import io
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Activity,
    ActivityLog,
    AdminAuditLog,
    GenerationRequest,
    SavedSuggestion,
    Suggestion,
)
from .serializers import (
    AdminAuditLogSerializer,
    ActivityLogCreateSerializer,
    ActivityLogSerializer,
    ActivitySerializer,
    GenerateInputSerializer,
    LoginSerializer,
    RegisterSerializer,
    SavedSuggestionCreateSerializer,
    SavedSuggestionSerializer,
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
COOLDOWN_NOTICE = "Nothing fresh from the last 7 days. We relaxed recency once."
RECENT_SUGGESTION_COOLDOWN_DAYS = 7


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


def _recent_activity_ids_for_user(user):
    cutoff = timezone.now() - timedelta(days=RECENT_SUGGESTION_COOLDOWN_DAYS)
    return list(
        Suggestion.objects.filter(
            request__user=user,
            created_at__gte=cutoff,
        )
        .values_list("activity_id", flat=True)
        .distinct()
    )


def _choose_activity(payload, *, exclude_ids=None, cooldown_ids=None):
    exclude_ids = set(exclude_ids or [])
    cooldown_ids = set(cooldown_ids or [])
    ranked_candidates, fallback_applied = _rank_candidate_activities(
        payload,
        exclude_ids=list(exclude_ids | cooldown_ids),
    )
    cooldown_relaxed = False

    if not ranked_candidates and cooldown_ids:
        ranked_candidates, fallback_applied = _rank_candidate_activities(
            payload,
            exclude_ids=list(exclude_ids),
        )
        cooldown_relaxed = bool(ranked_candidates)

    if not ranked_candidates:
        return None, False, False

    window_size = min(TOP_CANDIDATE_WINDOW, len(ranked_candidates))
    return random.choice(ranked_candidates[:window_size]), fallback_applied, cooldown_relaxed


def _normalized_money_value(value):
    number = float(value)
    if number.is_integer():
        return int(number)
    return round(number, 2)


def _build_explainability(payload, activity, *, fallback_applied, cooldown_relaxed):
    mood_token = _normalize_mood_level(payload["mood"])
    social_preference = payload["social_preference"]
    energy_match = _activity_matches_mood(activity, mood_token)
    social_match = _activity_matches_social(activity, social_preference)
    energy_score = 2 if energy_match else 0
    social_score = 1 if social_match else 0
    excluded_categories = payload.get("excluded_categories", [])
    category_matched = activity.category not in excluded_categories
    category_relaxed = fallback_applied and not category_matched

    return {
        "hard_constraints": {
            "time": {
                "matched": activity.min_time_minutes <= payload["time_minutes"],
                "required_minutes": int(payload["time_minutes"]),
                "activity_min_minutes": activity.min_time_minutes,
            },
            "budget": {
                "matched": float(activity.max_budget) <= float(payload["budget"]),
                "required_budget": _normalized_money_value(payload["budget"]),
                "activity_max_budget": _normalized_money_value(activity.max_budget),
            },
            "excluded_category": {
                "matched": category_matched,
                "relaxed": category_relaxed,
                "selected": excluded_categories,
                "activity_category": activity.category,
            },
        },
        "soft_preferences": {
            "energy": {
                "matched": energy_match,
                "score": energy_score,
                "weight": 2,
                "requested": mood_token,
                "activity_tags": [
                    _normalize_mood_level(tag) for tag in activity.mood_tags
                ],
            },
            "social": {
                "matched": social_match,
                "score": social_score,
                "weight": 1,
                "requested": social_preference,
                "activity_social": activity.social_type,
            },
            "total_score": energy_score + social_score,
            "max_score": 3,
        },
        "system": {
            "fallback_applied": fallback_applied,
            "cooldown_relaxed": cooldown_relaxed,
        },
    }


def _serialize_suggestion_response(
    suggestion,
    payload,
    *,
    fallback_applied=False,
    cooldown_relaxed=False,
):
    data = SuggestionSerializer(suggestion).data
    data["fallback_applied"] = fallback_applied
    data["fallback_message"] = FALLBACK_NOTICE if fallback_applied else ""
    data["cooldown_relaxed"] = cooldown_relaxed
    data["cooldown_message"] = COOLDOWN_NOTICE if cooldown_relaxed else ""
    data["explainability"] = _build_explainability(
        payload,
        suggestion.activity,
        fallback_applied=fallback_applied,
        cooldown_relaxed=cooldown_relaxed,
    )
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


class SavedSuggestionPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50


class AdminAuditLogPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


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

        selected_activity, fallback_applied, cooldown_relaxed = _choose_activity(
            payload,
            cooldown_ids=_recent_activity_ids_for_user(request.user),
        )
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
                payload,
                fallback_applied=fallback_applied,
                cooldown_relaxed=cooldown_relaxed,
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
        selected_activity, fallback_applied, cooldown_relaxed = _choose_activity(
            payload,
            exclude_ids=exclude_ids,
            cooldown_ids=_recent_activity_ids_for_user(request.user),
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
                payload,
                fallback_applied=fallback_applied,
                cooldown_relaxed=cooldown_relaxed,
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
            Suggestion.objects.filter(id=current_pending.suggestion_id).update(
                is_accepted=False
            )
            if current_pending.suggestion.request_id == suggestion.request_id:
                current_pending.delete()
            else:
                if not current_pending.comment:
                    current_pending.comment = (
                        "Auto-skipped after accepting a newer suggestion."
                    )
                current_pending.status = ActivityLog.Status.SKIPPED
                current_pending.rating = None
                current_pending.save(
                    update_fields=["status", "rating", "comment", "updated_at"]
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
        query = request.query_params.get("q", "").strip()
        sort = request.query_params.get("sort", "newest")
        valid_sorts = {"newest", "oldest", "title"}
        pending_log = _pending_activity_log_for_user(request.user)
        queryset = ActivityLog.objects.filter(user=request.user).exclude(
            status=ActivityLog.Status.ACCEPTED
        ).select_related("suggestion__activity")

        if query:
            queryset = queryset.filter(
                Q(suggestion__activity__title__icontains=query)
                | Q(comment__icontains=query)
            )

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

        if sort not in valid_sorts:
            return Response(
                {"sort": ["Invalid sort value. Use newest, oldest, or title."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if sort == "oldest":
            queryset = queryset.order_by("created_at")
        elif sort == "title":
            queryset = queryset.order_by("suggestion__activity__title", "-created_at")
        else:
            queryset = queryset.order_by("-created_at")

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


class SavedSuggestionListCreateView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = SavedSuggestionPagination

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        sort = request.query_params.get("sort", "newest")
        valid_sorts = {"newest", "oldest", "title"}
        queryset = SavedSuggestion.objects.filter(user=request.user).select_related(
            "suggestion__activity",
            "suggestion__request",
        )

        if query:
            queryset = queryset.filter(
                Q(suggestion__activity__title__icontains=query)
                | Q(suggestion__activity__description__icontains=query)
            )

        if sort not in valid_sorts:
            return Response(
                {"sort": ["Invalid sort value. Use newest, oldest, or title."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if sort == "oldest":
            queryset = queryset.order_by("created_at")
        elif sort == "title":
            queryset = queryset.order_by("suggestion__activity__title", "-created_at")
        else:
            queryset = queryset.order_by("-created_at")

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = SavedSuggestionSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = SavedSuggestionCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        saved_entry = serializer.save()
        output = SavedSuggestionSerializer(saved_entry)
        return Response(output.data, status=status.HTTP_201_CREATED)


class SavedSuggestionDetailView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, saved_id):
        saved_entry = get_object_or_404(
            SavedSuggestion,
            id=saved_id,
            user=request.user,
        )
        saved_entry.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def _parse_csv_bool(value, *, default=False):
    raw = str(value or "").strip().lower()
    if raw in {"1", "true", "yes", "y"}:
        return True
    if raw in {"0", "false", "no", "n"}:
        return False
    return default


def _parse_csv_mood_tags(value):
    if isinstance(value, list):
        raw_values = value
    else:
        raw = str(value or "").strip()
        if not raw:
            return []
        separator = "|" if "|" in raw else ","
        raw_values = raw.split(separator)

    parsed = []
    seen = set()
    for token in raw_values:
        normalized = _normalize_mood_level(token)
        if normalized in GenerationRequest.Mood.values and normalized not in seen:
            parsed.append(normalized)
            seen.add(normalized)
    return parsed


def _record_admin_audit(action, admin_user, *, target="", metadata=None):
    AdminAuditLog.objects.create(
        admin_user=admin_user,
        action=action,
        target=target,
        metadata=metadata or {},
    )


class AdminActivityCSVImportView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response(
                {"file": ["Upload a CSV file using the `file` field."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            content = uploaded_file.read().decode("utf-8-sig")
        except UnicodeDecodeError:
            return Response(
                {"file": ["CSV must be UTF-8 encoded."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reader = csv.DictReader(io.StringIO(content))
        if not reader.fieldnames:
            return Response(
                {"file": ["CSV header row is required."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        required_columns = {
            "title",
            "category",
            "min_time_minutes",
            "max_time_minutes",
            "min_budget",
            "max_budget",
        }
        missing_columns = sorted(required_columns - set(reader.fieldnames))
        if missing_columns:
            return Response(
                {
                    "file": [
                        f"Missing required columns: {', '.join(missing_columns)}"
                    ]
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        created = 0
        errors = []

        for row_index, row in enumerate(reader, start=2):
            payload = {
                "title": str(row.get("title", "")).strip(),
                "description": str(row.get("description", "")).strip(),
                "category": str(row.get("category", "")).strip().upper(),
                "min_time_minutes": row.get("min_time_minutes"),
                "max_time_minutes": row.get("max_time_minutes"),
                "min_budget": row.get("min_budget"),
                "max_budget": row.get("max_budget"),
                "mood_tags": _parse_csv_mood_tags(row.get("mood_tags")),
                "social_type": (
                    str(row.get("social_type", Activity.SocialType.EITHER))
                    .strip()
                    .upper()
                ),
                "is_outdoor": _parse_csv_bool(row.get("is_outdoor")),
                "is_active": _parse_csv_bool(row.get("is_active"), default=True),
            }
            serializer = ActivitySerializer(data=payload)

            if serializer.is_valid():
                serializer.save()
                created += 1
            else:
                errors.append(
                    {
                        "row": row_index,
                        "errors": serializer.errors,
                    }
                )

        response_payload = {
            "created": created,
            "failed": len(errors),
            "errors": errors[:50],
        }
        _record_admin_audit(
            AdminAuditLog.Action.IMPORT_CSV,
            request.user,
            target=f"file:{uploaded_file.name}",
            metadata={
                "created": created,
                "failed": len(errors),
                "rows_processed": created + len(errors),
            },
        )
        response_status = (
            status.HTTP_201_CREATED
            if not errors
            else status.HTTP_200_OK
        )
        return Response(response_payload, status=response_status)


class AdminActivityListCreateView(generics.ListCreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAdminUser]
    serializer_class = ActivitySerializer
    queryset = Activity.objects.all().order_by("title")


class AdminActivityDetailView(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAdminUser]
    serializer_class = ActivitySerializer
    queryset = Activity.objects.all()

    def destroy(self, request, *args, **kwargs):
        activity = self.get_object()
        metadata = {
            "activity_id": activity.id,
            "title": activity.title,
            "category": activity.category,
        }
        response = super().destroy(request, *args, **kwargs)
        _record_admin_audit(
            AdminAuditLog.Action.DELETE_ACTIVITY,
            request.user,
            target=f"activity:{metadata['activity_id']}",
            metadata=metadata,
        )
        return response


class AdminAuditLogListView(generics.ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAdminUser]
    serializer_class = AdminAuditLogSerializer
    pagination_class = AdminAuditLogPagination
    queryset = AdminAuditLog.objects.select_related("admin_user").all()
