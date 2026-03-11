import io
from datetime import timedelta

from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from .models import (
    Activity,
    ActivityLog,
    AdminAuditLog,
    GenerationRequest,
    SavedSuggestion,
    Suggestion,
)
from .views import _rank_candidate_activities

User = get_user_model()


class DailyRandomEventsAPITests(APITestCase):
    def setUp(self):
        self.user = self._create_user("member", "Member123456!")
        self.other_user = self._create_user("other", "Other123456!")
        self.admin_user = self._create_user(
            "adminuser",
            "Admin123456!",
            is_staff=True,
            is_superuser=True,
        )

        self.relaxed_indoor = self._create_activity(
            title="Visit a Bookstore",
            category="INDOOR",
            mood_tags=["low"],
        )
        self.relaxed_cafe = self._create_activity(
            title="Try a New Cafe",
            category="FOOD",
            mood_tags=["low"],
        )
        self.excluded_outdoor = self._create_activity(
            title="Take a Park Walk",
            category="OUTDOOR",
            mood_tags=["low"],
            is_outdoor=True,
        )
        self.energetic_option = self._create_activity(
            title="Quick Workout",
            category="FITNESS",
            mood_tags=["high"],
        )

    def _create_user(
        self,
        username,
        password,
        *,
        email=None,
        is_staff=False,
        is_superuser=False,
    ):
        return User.objects.create_user(
            username=username,
            email=email or f"{username}@example.com",
            password=password,
            is_staff=is_staff,
            is_superuser=is_superuser,
        )

    def _auth_client(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        return client

    def _create_activity(self, **overrides):
        defaults = {
            "title": "Sample Activity",
            "description": "A test activity.",
            "category": "GENERAL",
            "min_time_minutes": 30,
            "max_time_minutes": 90,
            "min_budget": "0.00",
            "max_budget": "20.00",
            "mood_tags": ["low"],
            "social_type": Activity.SocialType.EITHER,
            "is_outdoor": False,
            "is_active": True,
        }
        defaults.update(overrides)
        return Activity.objects.create(**defaults)

    def _default_generate_payload(self):
        return {
            "time_minutes": 60,
            "budget": "20.00",
            "mood": "low",
            "social_preference": "SOLO",
            "excluded_categories": ["OUTDOOR"],
        }

    def _create_request_for_user(self, user, **overrides):
        defaults = {
            "time_minutes": 60,
            "budget": "20.00",
            "mood": GenerationRequest.Mood.LOW,
            "social_preference": GenerationRequest.SocialPreference.SOLO,
            "excluded_categories": [],
        }
        defaults.update(overrides)
        return GenerationRequest.objects.create(user=user, **defaults)

    def test_register_returns_token_and_normalized_email(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "newmember",
                "email": "NEWMEMBER@EXAMPLE.COM",
                "password": "StrongPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["user"]["username"], "newmember")
        self.assertEqual(response.data["user"]["email"], "newmember@example.com")
        self.assertTrue(Token.objects.filter(user__username="newmember").exists())

    def test_login_returns_existing_token(self):
        response = self.client.post(
            "/api/auth/login/",
            {
                "username": "member",
                "password": "Member123456!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["user"]["username"], "member")
        self.assertFalse(response.data["user"]["is_staff"])

    @override_settings(DEMO_PASSWORD_RESET_LINKS=False)
    def test_password_reset_request_returns_generic_response_for_known_and_unknown_email(self):
        known_response = self.client.post(
            "/api/auth/password-reset/",
            {"email": self.user.email},
            format="json",
        )
        unknown_response = self.client.post(
            "/api/auth/password-reset/",
            {"email": "unknown@example.com"},
            format="json",
        )
        expected_message = (
            "If an account with that email exists, "
            "a password reset link has been generated."
        )

        self.assertEqual(known_response.status_code, status.HTTP_200_OK)
        self.assertEqual(unknown_response.status_code, status.HTTP_200_OK)
        self.assertEqual(known_response.data, {"message": expected_message})
        self.assertEqual(unknown_response.data, {"message": expected_message})

    @override_settings(
        DEMO_PASSWORD_RESET_LINKS=True,
        FRONTEND_BASE_URL="https://app.example.com",
    )
    def test_password_reset_demo_mode_always_returns_frontend_link_shape(self):
        existing_response = self.client.post(
            "/api/auth/password-reset/",
            {"email": self.user.email},
            format="json",
        )
        unknown_response = self.client.post(
            "/api/auth/password-reset/",
            {"email": "unknown@example.com"},
            format="json",
        )

        self.assertEqual(existing_response.status_code, status.HTTP_200_OK)
        self.assertEqual(unknown_response.status_code, status.HTTP_200_OK)
        self.assertIn("demo_link", existing_response.data)
        self.assertIn("demo_link", unknown_response.data)
        self.assertTrue(
            existing_response.data["demo_link"].startswith(
                "https://app.example.com/reset-password-confirm/"
            )
        )
        self.assertTrue(
            unknown_response.data["demo_link"].startswith(
                "https://app.example.com/reset-password-confirm/"
            )
        )

    def test_password_reset_confirm_rejects_weak_password(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        response = self.client.post(
            "/api/auth/password-reset-confirm/",
            {
                "uid": uid,
                "token": token,
                "new_password": "12345678",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("new_password", response.data)

    def test_password_reset_confirm_accepts_valid_password(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        response = self.client.post(
            "/api/auth/password-reset-confirm/",
            {
                "uid": uid,
                "token": token,
                "new_password": "NewStrongPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewStrongPass123!"))

    def test_metadata_requires_authentication(self):
        response = self.client.get("/api/metadata/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_generate_reroll_accept_and_log_workflow_matches_frontend_contract(self):
        client = self._auth_client(self.user)

        generate_response = client.post(
            "/api/generate/",
            self._default_generate_payload(),
            format="json",
        )
        self.assertEqual(generate_response.status_code, status.HTTP_201_CREATED)
        self.assertSetEqual(
            set(generate_response.data.keys()),
            {
                "id",
                "request_id",
                "rank_no",
                "is_accepted",
                "created_at",
                "activity",
                "fallback_applied",
                "fallback_message",
                "cooldown_relaxed",
                "cooldown_message",
                "explainability",
            },
        )
        self.assertIn("title", generate_response.data["activity"])
        self.assertFalse(generate_response.data["fallback_applied"])
        self.assertEqual(generate_response.data["fallback_message"], "")
        self.assertFalse(generate_response.data["cooldown_relaxed"])
        self.assertEqual(generate_response.data["cooldown_message"], "")
        self.assertIn("hard_constraints", generate_response.data["explainability"])
        self.assertIn("soft_preferences", generate_response.data["explainability"])
        self.assertIn("system", generate_response.data["explainability"])
        self.assertNotEqual(
            generate_response.data["activity"]["id"],
            self.excluded_outdoor.id,
        )

        first_suggestion = Suggestion.objects.get(id=generate_response.data["id"])
        first_accept_response = client.post(
            f"/api/suggestions/{first_suggestion.id}/accept/",
            {},
            format="json",
        )
        self.assertEqual(first_accept_response.status_code, status.HTTP_200_OK)
        self.assertTrue(first_accept_response.data["is_accepted"])
        self.assertTrue(
            ActivityLog.objects.filter(
                suggestion=first_suggestion,
                user=self.user,
                status=ActivityLog.Status.ACCEPTED,
            ).exists()
        )

        pending_response = client.get("/api/logs/?page=1")
        self.assertEqual(pending_response.status_code, status.HTTP_200_OK)
        self.assertEqual(pending_response.data["count"], 0)
        self.assertIsNotNone(pending_response.data["pending"])
        self.assertEqual(
            pending_response.data["pending"]["suggestion_id"],
            first_suggestion.id,
        )

        reroll_response = client.post(
            f"/api/generate/{generate_response.data['request_id']}/reroll/",
            {},
            format="json",
        )
        self.assertEqual(reroll_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(reroll_response.data["rank_no"], 2)
        self.assertIn("explainability", reroll_response.data)
        self.assertNotEqual(reroll_response.data["id"], first_suggestion.id)
        self.assertNotEqual(
            reroll_response.data["activity"]["id"],
            first_suggestion.activity_id,
        )

        second_suggestion = Suggestion.objects.get(id=reroll_response.data["id"])
        second_accept_response = client.post(
            f"/api/suggestions/{second_suggestion.id}/accept/",
            {},
            format="json",
        )
        self.assertEqual(second_accept_response.status_code, status.HTTP_200_OK)

        first_suggestion.refresh_from_db()
        second_suggestion.refresh_from_db()
        self.assertFalse(first_suggestion.is_accepted)
        self.assertTrue(second_suggestion.is_accepted)
        self.assertFalse(
            ActivityLog.objects.filter(suggestion=first_suggestion).exists()
        )
        self.assertTrue(
            ActivityLog.objects.filter(
                suggestion=second_suggestion,
                status=ActivityLog.Status.ACCEPTED,
            ).exists()
        )

        log_response = client.post(
            "/api/logs/",
            {
                "suggestion_id": second_suggestion.id,
                "status": ActivityLog.Status.COMPLETED,
                "rating": 5,
                "comment": "Fits the available time well.",
            },
            format="json",
        )
        self.assertEqual(log_response.status_code, status.HTTP_200_OK)
        self.assertEqual(log_response.data["suggestion_id"], second_suggestion.id)
        self.assertEqual(log_response.data["request_id"], generate_response.data["request_id"])
        self.assertEqual(log_response.data["activity"]["id"], second_suggestion.activity_id)
        self.assertEqual(log_response.data["status"], ActivityLog.Status.COMPLETED)

        history_response = client.get("/api/logs/?status=COMPLETED&page=1")
        self.assertEqual(history_response.status_code, status.HTTP_200_OK)
        self.assertEqual(history_response.data["count"], 1)
        self.assertEqual(len(history_response.data["results"]), 1)
        self.assertIsNone(history_response.data["pending"])
        self.assertEqual(
            history_response.data["results"][0]["suggestion_id"],
            second_suggestion.id,
        )

    def test_ranked_candidates_use_hard_limits_and_soft_scores(self):
        exact_match = self._create_activity(
            title="Exact Match",
            min_time_minutes=10,
            max_budget="10.00",
            category="INDOOR",
            mood_tags=["high"],
            social_type=Activity.SocialType.EITHER,
        )
        excluded_category = self._create_activity(
            title="Excluded Category Match",
            min_time_minutes=10,
            max_budget="10.00",
            category="OUTDOOR",
            mood_tags=["high"],
            social_type=Activity.SocialType.EITHER,
        )
        social_mismatch = self._create_activity(
            title="Social Mismatch",
            min_time_minutes=10,
            max_budget="10.00",
            category="INDOOR",
            mood_tags=["high"],
            social_type=Activity.SocialType.FRIENDS,
        )
        self._create_activity(
            title="Too Expensive",
            min_time_minutes=10,
            max_budget="11.00",
            category="INDOOR",
            mood_tags=["high"],
            social_type=Activity.SocialType.EITHER,
        )

        ranked = _rank_candidate_activities(
            {
                "time_minutes": 10,
                "budget": "10.00",
                "mood": "high",
                "social_preference": "SOLO",
                "excluded_categories": ["OUTDOOR"],
            }
        )

        ranked_ids = [activity.id for activity in ranked[0]]

        self.assertFalse(ranked[1])
        self.assertEqual(ranked_ids, [exact_match.id, social_mismatch.id])

    def test_ranked_candidates_relax_energy_before_social(self):
        social_match_only = self._create_activity(
            title="Social Match Only",
            min_time_minutes=10,
            max_budget="10.00",
            mood_tags=["low"],
            social_type=Activity.SocialType.EITHER,
        )
        hard_only = self._create_activity(
            title="Hard Limit Only",
            min_time_minutes=10,
            max_budget="10.00",
            mood_tags=["low"],
            social_type=Activity.SocialType.FRIENDS,
        )

        ranked = _rank_candidate_activities(
            {
                "time_minutes": 10,
                "budget": "10.00",
                "mood": "high",
                "social_preference": "SOLO",
                "excluded_categories": [],
            }
        )

        ranked_ids = [activity.id for activity in ranked[0]]

        self.assertFalse(ranked[1])
        self.assertEqual(
            ranked_ids,
            [social_match_only.id, hard_only.id],
        )

    def test_generate_falls_back_to_hard_limits_if_no_soft_matches_exist(self):
        client = self._auth_client(self.user)
        fallback = self._create_activity(
            title="Fallback Result",
            min_time_minutes=10,
            max_budget="10.00",
            mood_tags=["low"],
            social_type=Activity.SocialType.FRIENDS,
        )

        response = client.post(
            "/api/generate/",
            {
                "time_minutes": 10,
                "budget": "10.00",
                "mood": "high",
                "social_preference": "SOLO",
                "excluded_categories": [],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["activity"]["id"], fallback.id)
        self.assertFalse(response.data["fallback_applied"])

    def test_generate_relaxes_category_once_when_hard_filters_would_be_empty(self):
        client = self._auth_client(self.user)
        excluded_only = self._create_activity(
            title="Excluded Only Result",
            min_time_minutes=10,
            max_budget="10.00",
            category="FITNESS",
            mood_tags=["high"],
            social_type=Activity.SocialType.EITHER,
        )

        response = client.post(
            "/api/generate/",
            {
                "time_minutes": 10,
                "budget": "10.00",
                "mood": "high",
                "social_preference": "SOLO",
                "excluded_categories": ["FITNESS"],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["activity"]["id"], excluded_only.id)
        self.assertTrue(response.data["fallback_applied"])
        self.assertEqual(
            response.data["fallback_message"],
            "Nothing fits perfectly. We relaxed one preference.",
        )

    def test_log_validation_rejects_invalid_rating_and_duplicate_submissions(self):
        client = self._auth_client(self.user)
        generate_response = client.post(
            "/api/generate/",
            self._default_generate_payload(),
            format="json",
        )
        suggestion_id = generate_response.data["id"]
        client.post(
            f"/api/suggestions/{suggestion_id}/accept/",
            {},
            format="json",
        )

        invalid_response = client.post(
            "/api/logs/",
            {
                "suggestion_id": suggestion_id,
                "status": ActivityLog.Status.SKIPPED,
                "rating": 3,
                "comment": "Skipping this one.",
            },
            format="json",
        )
        self.assertEqual(invalid_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("rating", invalid_response.data)

        first_log_response = client.post(
            "/api/logs/",
            {
                "suggestion_id": suggestion_id,
                "status": ActivityLog.Status.SKIPPED,
                "comment": "Skipping this one.",
            },
            format="json",
        )
        self.assertEqual(first_log_response.status_code, status.HTTP_200_OK)

        duplicate_response = client.post(
            "/api/logs/",
            {
                "suggestion_id": suggestion_id,
                "status": ActivityLog.Status.SKIPPED,
                "comment": "Trying to submit twice.",
            },
            format="json",
        )
        self.assertEqual(duplicate_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("suggestion_id", duplicate_response.data)

    def test_logs_require_accept_before_outcome_is_recorded(self):
        client = self._auth_client(self.user)
        generate_response = client.post(
            "/api/generate/",
            self._default_generate_payload(),
            format="json",
        )

        response = client.post(
            "/api/logs/",
            {
                "suggestion_id": generate_response.data["id"],
                "status": ActivityLog.Status.COMPLETED,
                "rating": 4,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["suggestion_id"][0],
            "Accept the suggestion before logging an outcome.",
        )

    def test_user_can_delete_archived_and_pending_history_logs(self):
        client = self._auth_client(self.user)

        archived_generate = client.post(
            "/api/generate/",
            self._default_generate_payload(),
            format="json",
        )
        archived_suggestion_id = archived_generate.data["id"]
        client.post(
            f"/api/suggestions/{archived_suggestion_id}/accept/",
            {},
            format="json",
        )
        archived_log = client.post(
            "/api/logs/",
            {
                "suggestion_id": archived_suggestion_id,
                "status": ActivityLog.Status.COMPLETED,
                "rating": 4,
            },
            format="json",
        )
        self.assertEqual(archived_log.status_code, status.HTTP_200_OK)

        delete_archived = client.delete(f"/api/logs/{archived_log.data['id']}/")
        self.assertEqual(delete_archived.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ActivityLog.objects.filter(id=archived_log.data["id"]).exists())
        archived_suggestion = Suggestion.objects.get(id=archived_suggestion_id)
        self.assertFalse(archived_suggestion.is_accepted)

        pending_generate = client.post(
            "/api/generate/",
            self._default_generate_payload(),
            format="json",
        )
        pending_suggestion_id = pending_generate.data["id"]
        client.post(
            f"/api/suggestions/{pending_suggestion_id}/accept/",
            {},
            format="json",
        )
        pending_response = client.get("/api/logs/?page=1")
        pending_log_id = pending_response.data["pending"]["id"]

        delete_pending = client.delete(f"/api/logs/{pending_log_id}/")
        self.assertEqual(delete_pending.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ActivityLog.objects.filter(id=pending_log_id).exists())
        pending_suggestion = Suggestion.objects.get(id=pending_suggestion_id)
        self.assertFalse(pending_suggestion.is_accepted)

    def test_accept_new_suggestion_auto_skips_existing_pending_from_other_request(self):
        client = self._auth_client(self.user)

        first_response = client.post(
            "/api/generate/",
            self._default_generate_payload(),
            format="json",
        )
        first_suggestion_id = first_response.data["id"]
        accept_first = client.post(
            f"/api/suggestions/{first_suggestion_id}/accept/",
            {},
            format="json",
        )
        self.assertEqual(accept_first.status_code, status.HTTP_200_OK)

        second_response = client.post(
            "/api/generate/",
            self._default_generate_payload(),
            format="json",
        )
        second_suggestion_id = second_response.data["id"]
        accept_second = client.post(
            f"/api/suggestions/{second_suggestion_id}/accept/",
            {},
            format="json",
        )
        self.assertEqual(accept_second.status_code, status.HTTP_200_OK)

        first_suggestion = Suggestion.objects.get(id=first_suggestion_id)
        second_suggestion = Suggestion.objects.get(id=second_suggestion_id)
        self.assertFalse(first_suggestion.is_accepted)
        self.assertTrue(second_suggestion.is_accepted)

        first_log = ActivityLog.objects.get(suggestion=first_suggestion)
        second_log = ActivityLog.objects.get(suggestion=second_suggestion)
        self.assertEqual(first_log.status, ActivityLog.Status.SKIPPED)
        self.assertIn("Auto-skipped", first_log.comment)
        self.assertEqual(second_log.status, ActivityLog.Status.ACCEPTED)

    def test_logs_reject_invalid_status_filter(self):
        client = self._auth_client(self.user)

        response = client.get("/api/logs/?status=INVALID")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["status"][0],
            "Invalid status filter. Use COMPLETED or SKIPPED.",
        )

    def test_saved_suggestions_create_list_delete_and_allow_continued_generation(self):
        client = self._auth_client(self.user)
        payload = self._default_generate_payload()

        generate_response = client.post("/api/generate/", payload, format="json")
        self.assertEqual(generate_response.status_code, status.HTTP_201_CREATED)
        suggestion_id = generate_response.data["id"]

        save_response = client.post(
            "/api/saved/",
            {"suggestion_id": suggestion_id},
            format="json",
        )
        self.assertEqual(save_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(save_response.data["suggestion_id"], suggestion_id)
        self.assertIn("activity", save_response.data)
        self.assertFalse(
            ActivityLog.objects.filter(
                suggestion_id=suggestion_id,
                status=ActivityLog.Status.ACCEPTED,
            ).exists()
        )

        second_generate = client.post("/api/generate/", payload, format="json")
        self.assertEqual(second_generate.status_code, status.HTTP_201_CREATED)

        duplicate_save = client.post(
            "/api/saved/",
            {"suggestion_id": suggestion_id},
            format="json",
        )
        self.assertEqual(duplicate_save.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("suggestion_id", duplicate_save.data)

        list_response = client.get("/api/saved/?page=1")
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data["count"], 1)
        saved_id = list_response.data["results"][0]["id"]

        delete_response = client.delete(f"/api/saved/{saved_id}/")
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(SavedSuggestion.objects.filter(id=saved_id).exists())

    def test_saved_suggestions_reject_other_users_suggestion(self):
        owner_client = self._auth_client(self.user)
        other_client = self._auth_client(self.other_user)
        payload = self._default_generate_payload()

        generate_response = owner_client.post("/api/generate/", payload, format="json")
        self.assertEqual(generate_response.status_code, status.HTTP_201_CREATED)

        save_response = other_client.post(
            "/api/saved/",
            {"suggestion_id": generate_response.data["id"]},
            format="json",
        )
        self.assertEqual(save_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_saved_suggestions_support_search_and_sort(self):
        client = self._auth_client(self.user)
        request = self._create_request_for_user(self.user)
        alpha = self._create_activity(
            title="Alpha Calm Walk",
            description="A calm route around the block.",
            min_time_minutes=10,
            max_budget="5.00",
            mood_tags=["low"],
            social_type=Activity.SocialType.EITHER,
        )
        beta = self._create_activity(
            title="Beta Tea Break",
            description="Tea and a short journal.",
            min_time_minutes=10,
            max_budget="5.00",
            mood_tags=["low"],
            social_type=Activity.SocialType.EITHER,
        )
        alpha_suggestion = Suggestion.objects.create(
            request=request,
            activity=alpha,
            rank_no=1,
        )
        beta_suggestion = Suggestion.objects.create(
            request=request,
            activity=beta,
            rank_no=2,
        )
        older = timezone.now() - timedelta(days=2)
        newer = timezone.now() - timedelta(days=1)
        SavedSuggestion.objects.create(user=self.user, suggestion=beta_suggestion)
        first_saved = SavedSuggestion.objects.create(user=self.user, suggestion=alpha_suggestion)
        SavedSuggestion.objects.filter(id=first_saved.id).update(created_at=older)
        SavedSuggestion.objects.filter(suggestion=beta_suggestion).update(created_at=newer)

        newest = client.get("/api/saved/?sort=newest")
        self.assertEqual(newest.status_code, status.HTTP_200_OK)
        self.assertEqual(newest.data["results"][0]["activity"]["title"], "Beta Tea Break")

        oldest = client.get("/api/saved/?sort=oldest")
        self.assertEqual(oldest.status_code, status.HTTP_200_OK)
        self.assertEqual(oldest.data["results"][0]["activity"]["title"], "Alpha Calm Walk")

        title_sorted = client.get("/api/saved/?sort=title")
        self.assertEqual(title_sorted.status_code, status.HTTP_200_OK)
        self.assertEqual(title_sorted.data["results"][0]["activity"]["title"], "Alpha Calm Walk")

        search = client.get("/api/saved/?q=journal")
        self.assertEqual(search.status_code, status.HTTP_200_OK)
        self.assertEqual(search.data["count"], 1)
        self.assertEqual(search.data["results"][0]["activity"]["title"], "Beta Tea Break")

    def test_logs_support_search_and_sort(self):
        client = self._auth_client(self.user)
        request_one = self._create_request_for_user(self.user)
        request_two = self._create_request_for_user(self.user)
        alpha = self._create_activity(
            title="Alpha Stretch",
            description="Stretch and reset.",
            min_time_minutes=10,
            max_budget="5.00",
            mood_tags=["low"],
            social_type=Activity.SocialType.EITHER,
        )
        beta = self._create_activity(
            title="Beta Journal",
            description="Write a short page.",
            min_time_minutes=10,
            max_budget="5.00",
            mood_tags=["low"],
            social_type=Activity.SocialType.EITHER,
        )
        alpha_suggestion = Suggestion.objects.create(
            request=request_one,
            activity=alpha,
            rank_no=1,
            is_accepted=True,
        )
        beta_suggestion = Suggestion.objects.create(
            request=request_two,
            activity=beta,
            rank_no=1,
            is_accepted=True,
        )

        first_log = ActivityLog.objects.create(
            user=self.user,
            suggestion=alpha_suggestion,
            status=ActivityLog.Status.COMPLETED,
            rating=4,
            comment="cozy routine",
        )
        second_log = ActivityLog.objects.create(
            user=self.user,
            suggestion=beta_suggestion,
            status=ActivityLog.Status.SKIPPED,
            comment="too late today",
        )
        older = timezone.now() - timedelta(days=2)
        newer = timezone.now() - timedelta(days=1)
        ActivityLog.objects.filter(id=first_log.id).update(created_at=older)
        ActivityLog.objects.filter(id=second_log.id).update(created_at=newer)

        newest = client.get("/api/logs/?sort=newest")
        self.assertEqual(newest.status_code, status.HTTP_200_OK)
        self.assertEqual(newest.data["results"][0]["activity"]["title"], "Beta Journal")

        oldest = client.get("/api/logs/?sort=oldest")
        self.assertEqual(oldest.status_code, status.HTTP_200_OK)
        self.assertEqual(oldest.data["results"][0]["activity"]["title"], "Alpha Stretch")

        title_sorted = client.get("/api/logs/?sort=title")
        self.assertEqual(title_sorted.status_code, status.HTTP_200_OK)
        self.assertEqual(title_sorted.data["results"][0]["activity"]["title"], "Alpha Stretch")

        search = client.get("/api/logs/?q=cozy")
        self.assertEqual(search.status_code, status.HTTP_200_OK)
        self.assertEqual(search.data["count"], 1)
        self.assertEqual(search.data["results"][0]["activity"]["title"], "Alpha Stretch")

        invalid_sort = client.get("/api/logs/?sort=priority")
        self.assertEqual(invalid_sort.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            invalid_sort.data["sort"][0],
            "Invalid sort value. Use newest, oldest, or title.",
        )

    def test_generate_avoids_recent_duplicates_within_7_day_window(self):
        client = self._auth_client(self.user)
        recent_activity = self._create_activity(
            title="Recent Option",
            category="TEST",
            min_time_minutes=10,
            max_budget="5.00",
            mood_tags=["low"],
            social_type=Activity.SocialType.EITHER,
        )
        fresh_activity = self._create_activity(
            title="Fresh Option",
            category="TEST",
            min_time_minutes=10,
            max_budget="5.00",
            mood_tags=["low"],
            social_type=Activity.SocialType.EITHER,
        )
        request = self._create_request_for_user(
            self.user,
            time_minutes=10,
            budget="5.00",
            mood=GenerationRequest.Mood.LOW,
            social_preference=GenerationRequest.SocialPreference.SOLO,
        )
        recent_suggestion = Suggestion.objects.create(
            request=request,
            activity=recent_activity,
            rank_no=1,
        )
        Suggestion.objects.filter(id=recent_suggestion.id).update(
            created_at=timezone.now() - timedelta(days=1)
        )

        response = client.post(
            "/api/generate/",
            {
                "time_minutes": 10,
                "budget": "5.00",
                "mood": "low",
                "social_preference": "SOLO",
                "excluded_categories": [],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["activity"]["id"], fresh_activity.id)
        self.assertFalse(response.data["cooldown_relaxed"])
        self.assertEqual(response.data["cooldown_message"], "")

    def test_generate_relaxes_cooldown_once_when_only_recent_activity_exists(self):
        client = self._auth_client(self.user)
        only_option = self._create_activity(
            title="Only Cooldown Candidate",
            category="TEST",
            min_time_minutes=10,
            max_budget="5.00",
            mood_tags=["low"],
            social_type=Activity.SocialType.EITHER,
        )
        request = self._create_request_for_user(
            self.user,
            time_minutes=10,
            budget="5.00",
            mood=GenerationRequest.Mood.LOW,
            social_preference=GenerationRequest.SocialPreference.SOLO,
        )
        recent_suggestion = Suggestion.objects.create(
            request=request,
            activity=only_option,
            rank_no=1,
        )
        Suggestion.objects.filter(id=recent_suggestion.id).update(
            created_at=timezone.now() - timedelta(days=1)
        )

        response = client.post(
            "/api/generate/",
            {
                "time_minutes": 10,
                "budget": "5.00",
                "mood": "low",
                "social_preference": "SOLO",
                "excluded_categories": [],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["activity"]["id"], only_option.id)
        self.assertTrue(response.data["cooldown_relaxed"])
        self.assertEqual(
            response.data["cooldown_message"],
            "Nothing fresh from the last 7 days. We relaxed recency once.",
        )

    def test_regular_user_cannot_access_admin_activity_endpoint(self):
        member_client = self._auth_client(self.user)
        admin_client = self._auth_client(self.admin_user)

        forbidden_response = member_client.get("/api/admin/activities/")
        self.assertEqual(forbidden_response.status_code, status.HTTP_403_FORBIDDEN)

        allowed_response = admin_client.get("/api/admin/activities/")
        self.assertEqual(allowed_response.status_code, status.HTTP_200_OK)
        self.assertEqual(allowed_response.data["count"], Activity.objects.count())
        self.assertLessEqual(len(allowed_response.data["results"]), 4)

    def test_admin_can_delete_and_import_activities_via_csv(self):
        admin_client = self._auth_client(self.admin_user)
        target = self._create_activity(
            title="Delete Via Admin",
            category="INDOOR",
            mood_tags=["medium"],
        )

        delete_response = admin_client.delete(f"/api/admin/activities/{target.id}/")
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Activity.objects.filter(id=target.id).exists())
        self.assertTrue(
            AdminAuditLog.objects.filter(
                action=AdminAuditLog.Action.DELETE_ACTIVITY,
                admin_user=self.admin_user,
                target=f"activity:{target.id}",
            ).exists()
        )

        csv_payload = (
            "title,description,category,min_time_minutes,max_time_minutes,"
            "min_budget,max_budget,mood_tags,social_type,is_outdoor,is_active\n"
            "CSV Activity,Imported by test,FOOD,15,45,5,18,low|medium,EITHER,false,true\n"
        )
        upload = io.BytesIO(csv_payload.encode("utf-8"))
        upload.name = "activities.csv"

        import_response = admin_client.post(
            "/api/admin/activities/import-csv/",
            {"file": upload},
            format="multipart",
        )
        self.assertEqual(import_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(import_response.data["created"], 1)
        self.assertEqual(import_response.data["failed"], 0)
        self.assertTrue(Activity.objects.filter(title="CSV Activity").exists())
        self.assertTrue(
            AdminAuditLog.objects.filter(
                action=AdminAuditLog.Action.IMPORT_CSV,
                admin_user=self.admin_user,
                target="file:activities.csv",
            ).exists()
        )

        audit_response = admin_client.get("/api/admin/audit-logs/?page=1")
        self.assertEqual(audit_response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(audit_response.data["count"], 2)
        self.assertIn("action", audit_response.data["results"][0])

    def test_regular_user_cannot_access_admin_audit_logs(self):
        member_client = self._auth_client(self.user)
        response = member_client.get("/api/admin/audit-logs/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_users_cannot_log_other_users_suggestions(self):
        owner_client = self._auth_client(self.user)
        other_client = self._auth_client(self.other_user)

        generate_response = owner_client.post(
            "/api/generate/",
            self._default_generate_payload(),
            format="json",
        )

        response = other_client.post(
            "/api/logs/",
            {
                "suggestion_id": generate_response.data["id"],
                "status": ActivityLog.Status.COMPLETED,
                "rating": 4,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["suggestion_id"][0],
            "You can only log your own suggestions.",
        )
