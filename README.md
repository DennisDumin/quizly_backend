# Quizly API

Quizly is a Django REST Framework backend that creates quizzes from YouTube
videos. The API downloads the video audio with `yt-dlp`, transcribes it with
Whisper, sends the transcript to Gemini, and stores the generated quiz and
questions for the authenticated user.

This repository contains only the backend. Do not commit frontend files,
`.env`, `db.sqlite3`, `media/`, downloaded audio, or local virtual environments.

## Tech Stack

- Python 3.12+
- Django 6
- Django REST Framework
- Simple JWT with HTTP-only auth cookies
- yt-dlp for YouTube audio downloads
- openai-whisper for transcription
- google-genai for Gemini quiz generation
- SQLite for local development

## Setup

1. Create and activate a virtual environment.

```powershell
python -m venv env
.\env\Scripts\Activate.ps1
```

2. Install the dependencies.

```powershell
pip install -r requirements.txt
```

3. Create your local environment file.

```powershell
Copy-Item .env.example .env
```

4. Add your real values to `.env`.

```env
SECRET_KEY=your_django_secret_key
DEBUG=True
GEMINI_API_KEY=your_gemini_api_key
ALLOWED_HOSTS=127.0.0.1,localhost
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

5. Install FFmpeg and make sure it is available in your system `PATH`.

Whisper and yt-dlp need FFmpeg to extract and process audio files.

6. Run migrations and create an admin user.

```powershell
python manage.py migrate
python manage.py createsuperuser
```

7. Start the backend.

```powershell
python manage.py runserver
```

The API is available at `http://127.0.0.1:8000/`.

## Environment Variables

| Name | Required | Description |
| --- | --- | --- |
| `SECRET_KEY` | Yes | Django secret key for the local project. |
| `DEBUG` | Yes | Use `True` for local development. |
| `GEMINI_API_KEY` | Yes | API key from Google AI Studio. |
| `ALLOWED_HOSTS` | Yes | Comma-separated Django host allowlist. |
| `CORS_ALLOWED_ORIGINS` | Yes | Comma-separated frontend origins allowed by CORS. |

## Authentication

Authentication uses JWT tokens stored in HTTP-only cookies:

- `access_token` authenticates API requests.
- `refresh_token` is used by `/api/token/refresh/`.

Logout deletes both cookies and blacklists the refresh token.

## Endpoints

### Auth

| Method | Path | Description | Auth |
| --- | --- | --- | --- |
| `POST` | `/api/register/` | Register a user. | No |
| `POST` | `/api/login/` | Login and set auth cookies. | No |
| `POST` | `/api/logout/` | Logout and invalidate refresh token. | Yes |
| `POST` | `/api/token/refresh/` | Create a new access cookie. | Refresh cookie |

### Quizzes

| Method | Path | Description | Auth |
| --- | --- | --- | --- |
| `GET` | `/api/quizzes/` | List the current user's quizzes. | Yes |
| `POST` | `/api/quizzes/` | Create a quiz from a YouTube URL. | Yes |
| `GET` | `/api/quizzes/{id}/` | Retrieve one quiz. | Yes |
| `PATCH` | `/api/quizzes/{id}/` | Update quiz title or description. | Yes |
| `DELETE` | `/api/quizzes/{id}/` | Delete one quiz. | Yes |

### Example Quiz Creation

```http
POST /api/quizzes/
Content-Type: application/json

{
  "url": "https://www.youtube.com/watch?v=example"
}
```

Successful response: `201 Created`

```json
{
  "id": 1,
  "title": "Quiz Title",
  "description": "Quiz Description",
  "created_at": "2026-06-07T12:00:00Z",
  "updated_at": "2026-06-07T12:00:00Z",
  "video_url": "https://www.youtube.com/watch?v=example",
  "questions": [
    {
      "id": 1,
      "question_title": "Question text",
      "question_options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Option A",
      "created_at": "2026-06-07T12:00:00Z",
      "updated_at": "2026-06-07T12:00:00Z"
    }
  ]
}
```

## Development Checks

Run the Django system check:

```powershell
python manage.py check
```

Run the test suite:

```powershell
python manage.py test
```

## Admin

The Django admin is enabled at `/admin/`. Use `python manage.py createsuperuser`
to create a local admin account. Quizzes and questions can be inspected there.
