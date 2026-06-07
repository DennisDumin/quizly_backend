from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Question, Quiz


TEST_SIMPLE_JWT = {
    **settings.SIMPLE_JWT,
    "SIGNING_KEY": "test-secret-key-with-at-least-32-characters",
}


def create_user(username):
    """Creates a reusable quiz test user."""
    return User.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="StrongPass123!",
    )


def authenticated_client(user):
    """Returns an API client with access-token authentication."""
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.cookies[settings.ACCESS_TOKEN_COOKIE_NAME] = str(refresh.access_token)
    return client


def create_quiz(user, title="Python Basics", video_url="https://youtu.be/test"):
    """Creates a quiz with one question."""
    quiz = Quiz.objects.create(
        user=user,
        title=title,
        description="A short generated quiz.",
        video_url=video_url,
    )
    create_question(quiz)
    return quiz


def create_question(quiz):
    """Creates one multiple-choice question."""
    return Question.objects.create(
        quiz=quiz,
        question_title="What is Python?",
        question_options=["Language", "Animal", "Editor", "Browser"],
        answer="Language",
    )


def create_generated_quiz(user, url):
    """Builds a quiz returned by the mocked generation pipeline."""
    return create_quiz(user, title="Generated Quiz", video_url=url)


@override_settings(SIMPLE_JWT=TEST_SIMPLE_JWT)
class QuizEndpointTests(TestCase):
    """Covers the documented quiz endpoints."""

    def setUp(self):
        self.user = create_user("owner")
        self.other_user = create_user("other")
        self.client = authenticated_client(self.user)

    def test_list_returns_only_user_quizzes(self):
        quiz = create_quiz(self.user)
        create_quiz(self.other_user, title="Hidden")

        response = self.client.get("/api/quizzes/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], quiz.id)

    def test_retrieve_returns_owned_quiz(self):
        quiz = create_quiz(self.user)

        response = self.client.get(f"/api/quizzes/{quiz.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], quiz.title)
        self.assertEqual(len(response.data["questions"]), 1)

    def test_retrieve_rejects_other_user_quiz(self):
        quiz = create_quiz(self.other_user)

        response = self.client.get(f"/api/quizzes/{quiz.id}/")

        self.assertEqual(response.status_code, 403)

    def test_partial_update_changes_owned_quiz(self):
        quiz = create_quiz(self.user)

        response = self.client.patch(
            f"/api/quizzes/{quiz.id}/",
            {"title": "Updated Title"},
            format="json",
        )

        quiz.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(quiz.title, "Updated Title")

    def test_delete_removes_owned_quiz(self):
        quiz = create_quiz(self.user)

        response = self.client.delete(f"/api/quizzes/{quiz.id}/")

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Quiz.objects.filter(id=quiz.id).exists())

    @patch("quiz_app.api.views.create_quiz_from_youtube_url")
    def test_create_generates_quiz_from_youtube_url(self, mock_create):
        url = "https://www.youtube.com/watch?v=abc123"
        mock_create.side_effect = create_generated_quiz

        response = self.client.post("/api/quizzes/", {"url": url}, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["video_url"], url)
        self.assertEqual(response.data["title"], "Generated Quiz")

    def test_create_rejects_non_youtube_url(self):
        response = self.client.post(
            "/api/quizzes/",
            {"url": "https://example.com/video"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
