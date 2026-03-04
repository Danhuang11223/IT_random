# Daily Random Events API

This module assumes `Django`, `djangorestframework`, and `rest_framework.authtoken` are installed and enabled.

## Setup Notes

- Add `rest_framework`, `rest_framework.authtoken`, and `daily_random_events` to `INSTALLED_APPS`.
- Run migrations after adding the app.
- Wire `daily_random_events.urls` into the project-level `urls.py`, for example under `/api/`.
- Recommended DRF defaults:

```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}
```

## Authentication

- Auth scheme: token-based.
- Register or login returns a token string.
- Send the token in every protected request:

```http
Authorization: Token <token>
```

## Pagination

- `GET /api/logs/` uses page-number pagination.
- Query params:
  - `page`: 1-based page number.
  - `page_size`: optional, default `10`, max `50`.
- Response shape:

```json
{
  "count": 23,
  "next": "http://localhost:8000/api/logs/?page=2",
  "previous": null,
  "pending": null,
  "results": []
}
```

## Error Model

The API uses DRF's default error payloads.

Validation error example (`400`):

```json
{
  "budget": [
    "Ensure this value is greater than or equal to 0."
  ]
}
```

General error example (`401` / `403` / `404`):

```json
{
  "detail": "Authentication credentials were not provided."
}
```

## Status Codes

- `200 OK`: successful read or update-like action.
- `201 Created`: resource created (`register`, `generate`, `reroll`).
- `400 Bad Request`: invalid payload, duplicate log, invalid field combinations.
- `401 Unauthorized`: missing or invalid token.
- `403 Forbidden`: authenticated but lacks admin permission.
- `404 Not Found`: resource not found, or no matching activity exists for current constraints.

## Endpoints

### `POST /api/auth/register/`

Create a user and return a token.

Request:

```json
{
  "username": "alice",
  "email": "alice@example.com",
  "password": "StrongPass123"
}
```

Success `201`:

```json
{
  "token": "8c0d92d91d4d6cb7f5...",
  "user": {
    "id": 1,
    "username": "alice",
    "email": "alice@example.com"
  }
}
```

Common errors:

- `400` if username already exists.
- `400` if password is too short.

### `POST /api/auth/login/`

Login and return a token for an existing user.

Request:

```json
{
  "username": "alice",
  "password": "StrongPass123"
}
```

Success `200`:

```json
{
  "token": "8c0d92d91d4d6cb7f5...",
  "user": {
    "id": 1,
    "username": "alice",
    "email": "alice@example.com"
  }
}
```

Common errors:

- `401` for invalid username/password.

### `GET /api/metadata/`

Return front-end option lists for filters.

Auth: required.

Success `200`:

```json
{
  "categories": ["FOOD", "INDOOR", "OUTDOOR"],
  "moods": ["low", "medium", "high"],
  "social_preferences": ["SOLO", "FRIENDS", "EITHER"]
}
```

### `POST /api/generate/`

Create a generation request and return the first suggestion.

Auth: required.

Request:

```json
{
  "time_minutes": 90,
  "budget": "50.00",
  "mood": "medium",
  "social_preference": "SOLO",
  "excluded_categories": ["OUTDOOR"]
}
```

Success `201`:

```json
{
  "id": 3,
  "request_id": 7,
  "rank_no": 1,
  "is_accepted": false,
  "created_at": "2026-03-03T10:15:00Z",
  "activity": {
    "id": 8,
    "title": "Visit a nearby bookstore",
    "description": "Spend an hour browsing and pick one book.",
    "category": "INDOOR",
    "min_time_minutes": 30,
    "max_time_minutes": 120,
    "min_budget": "0.00",
    "max_budget": "30.00",
    "mood_tags": ["low", "medium"],
    "social_type": "SOLO",
    "is_outdoor": false,
    "is_active": true
  }
}
```

Common errors:

- `400` for invalid `mood`, invalid `social_preference`, negative budget, or malformed categories.
- `404` if no activity matches the constraints.

### `POST /api/generate/{request_id}/reroll/`

Generate another suggestion under the same request.

Auth: required.

Behavior:

- Reuses the stored constraints from the original request.
- Excludes activities already suggested in that request.
- Increments `rank_no`.

Success `201`:

```json
{
  "id": 4,
  "request_id": 7,
  "rank_no": 2,
  "is_accepted": false,
  "created_at": "2026-03-03T10:16:00Z",
  "activity": {
    "id": 11,
    "title": "Try a new cafe and journal",
    "description": "Order one drink and write for 30 minutes.",
    "category": "FOOD",
    "min_time_minutes": 30,
    "max_time_minutes": 90,
    "min_budget": "5.00",
    "max_budget": "25.00",
    "mood_tags": ["low"],
    "social_type": "SOLO",
    "is_outdoor": false,
    "is_active": true
  }
}
```

Common errors:

- `404` if the request does not belong to the current user.
- `404` if no new candidate remains after excluding previous suggestions.

### `POST /api/suggestions/{suggestion_id}/accept/`

Mark a suggestion as the chosen one for its request.

Auth: required.

Behavior:

- Marks this suggestion as `is_accepted = true`.
- Creates a pending history item with status `ACCEPTED`.
- Automatically clears a previous pending acceptance only when switching suggestions within the same generation request.
- Rejects the request if the user already has a pending accepted activity from another request.

Success `200`:

```json
{
  "id": 4,
  "request_id": 7,
  "rank_no": 2,
  "is_accepted": true,
  "created_at": "2026-03-03T10:16:00Z",
  "activity": {
    "id": 11,
    "title": "Try a new cafe and journal",
    "description": "Order one drink and write for 30 minutes.",
    "category": "FOOD",
    "min_time_minutes": 30,
    "max_time_minutes": 90,
    "min_budget": "5.00",
    "max_budget": "25.00",
    "mood_tags": ["low"],
    "social_type": "SOLO",
    "is_outdoor": false,
    "is_active": true
  }
}
```

Common errors:

- `404` if the suggestion does not belong to the current user.

### `GET /api/logs/`

List the current user's archived activity history.

Auth: required.

Query params:

- `page`
- `page_size`

Success `200`:

```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "pending": {
    "id": 9,
    "suggestion_id": 4,
    "request_id": 7,
    "status": "ACCEPTED",
    "rating": null,
    "comment": "",
    "created_at": "2026-03-03T10:20:00Z",
    "updated_at": "2026-03-03T10:20:00Z",
    "activity": {
      "id": 11,
      "title": "Try a new cafe and journal",
      "description": "Order one drink and write for 30 minutes.",
      "category": "FOOD",
      "min_time_minutes": 30,
      "max_time_minutes": 90,
      "min_budget": "5.00",
      "max_budget": "25.00",
      "mood_tags": ["low"],
      "social_type": "SOLO",
      "is_outdoor": false,
      "is_active": true
    }
  },
  "results": [
    {
      "id": 5,
      "suggestion_id": 4,
      "request_id": 7,
      "status": "COMPLETED",
      "rating": 4,
      "comment": "Good low-effort weekend idea.",
      "created_at": "2026-03-03T12:00:00Z",
      "updated_at": "2026-03-03T12:00:00Z",
      "activity": {
        "id": 11,
        "title": "Try a new cafe and journal",
        "description": "Order one drink and write for 30 minutes.",
        "category": "FOOD",
        "min_time_minutes": 30,
        "max_time_minutes": 90,
        "min_budget": "5.00",
        "max_budget": "25.00",
        "mood_tags": ["low"],
        "social_type": "SOLO",
        "is_outdoor": false,
        "is_active": true
      }
    }
  ]
}
```

Notes:

- `results` only contains archived items (`COMPLETED` / `SKIPPED`).
- `pending` contains the currently accepted activity waiting to be marked complete or skipped, or `null`.

### `POST /api/logs/`

Finalize a pending accepted history record.

Auth: required.

Request:

```json
{
  "suggestion_id": 4,
  "status": "COMPLETED",
  "rating": 4,
  "comment": "Good low-effort weekend idea."
}
```

Success `200`:

```json
{
  "id": 5,
  "suggestion_id": 4,
  "request_id": 7,
  "status": "COMPLETED",
  "rating": 4,
  "comment": "Good low-effort weekend idea.",
  "created_at": "2026-03-03T12:00:00Z",
  "updated_at": "2026-03-03T12:00:00Z",
  "activity": {
    "id": 11,
    "title": "Try a new cafe and journal",
    "description": "Order one drink and write for 30 minutes.",
    "category": "FOOD",
    "min_time_minutes": 30,
    "max_time_minutes": 90,
    "min_budget": "5.00",
    "max_budget": "25.00",
    "mood_tags": ["low"],
    "social_type": "SOLO",
    "is_outdoor": false,
    "is_active": true
  }
}
```

Valid combinations:

- `COMPLETED` may include `rating` and `comment`.
- `SKIPPED` may include `comment`, but `rating` must be omitted.

Common errors:

- `400` if `suggestion_id` belongs to another user.
- `400` if the suggestion has not been accepted yet.
- `400` if the same suggestion was already logged.
- `400` if `status` is `SKIPPED` and `rating` is provided.

### `DELETE /api/logs/{id}/`

Delete one history record.

Auth: required.

Behavior:

- Deletes the specified history record if it belongs to the current user.
- If the record is the current pending item, it also clears the related suggestion's accepted state.
- Deleting an archived record removes it from the user's history list.

Success `204`: empty response body.

Common errors:

- `404` if the log does not belong to the current user or does not exist.

### `GET /api/admin/activities/`

List all activities for admin management.

Auth: admin token required.

Success `200`:

```json
[
  {
    "id": 8,
    "title": "Visit a nearby bookstore",
    "description": "Spend an hour browsing and pick one book.",
    "category": "INDOOR",
    "min_time_minutes": 30,
    "max_time_minutes": 120,
    "min_budget": "0.00",
    "max_budget": "30.00",
    "mood_tags": ["low", "medium"],
    "social_type": "SOLO",
    "is_outdoor": false,
    "is_active": true
  }
]
```

### `POST /api/admin/activities/`

Create a new activity.

Auth: admin token required.

Request:

```json
{
  "title": "Walk a new neighborhood route",
  "description": "Take a 45-minute walk somewhere unfamiliar nearby.",
  "category": "OUTDOOR",
  "min_time_minutes": 30,
  "max_time_minutes": 90,
  "min_budget": "0.00",
  "max_budget": "0.00",
  "mood_tags": ["high", "low"],
  "social_type": "EITHER",
  "is_outdoor": true,
  "is_active": true
}
```

Success `201`: returns the created activity object.

### `GET /api/admin/activities/{id}/`

Retrieve one activity.

Auth: admin token required.

### `PATCH /api/admin/activities/{id}/`

Update part of an activity.

Auth: admin token required.

Request:

```json
{
  "is_active": false
}
```

Success `200`: returns the updated activity object.
