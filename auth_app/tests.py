from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken


TEST_SIMPLE_JWT = {
    **settings.SIMPLE_JWT,
    "SIGNING_KEY": "test-secret-key-with-at-least-32-characters",
}


def user_payload(username="new-user"):
    """Returns valid registration data."""
    return {
        "username": username,
        "email": f"{username}@example.com",
        "password": "StrongPass123!",
        "confirmed_password": "StrongPass123!",
    }


def create_user(username="existing-user"):
    """Creates a reusable test user."""
    return User.objects.create_user(
        username=username,
        email=f"{username}@example.com",
        password="StrongPass123!",
    )


def authenticate_client(client, user):
    """Adds JWT auth cookies to an API client."""
    refresh = RefreshToken.for_user(user)
    client.cookies[settings.ACCESS_TOKEN_COOKIE_NAME] = str(refresh.access_token)
    client.cookies[settings.REFRESH_TOKEN_COOKIE_NAME] = str(refresh)


@override_settings(SIMPLE_JWT=TEST_SIMPLE_JWT)
class AuthEndpointTests(TestCase):
    """Covers the documented authentication endpoints."""

    def setUp(self):
        self.client = APIClient()

    def test_register_creates_user(self):
        response = self.client.post("/api/register/", user_payload(), format="json")

        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(username="new-user").exists())
        self.assertEqual(response.data["detail"], "User created successfully!")

    def test_login_sets_auth_cookies(self):
        create_user()

        response = self.client.post(
            "/api/login/",
            {"username": "existing-user", "password": "StrongPass123!"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(settings.ACCESS_TOKEN_COOKIE_NAME, response.cookies)
        self.assertIn(settings.REFRESH_TOKEN_COOKIE_NAME, response.cookies)
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)
        self.assertEqual(response.data["user"]["username"], "existing-user")

    def test_login_rejects_invalid_credentials(self):
        create_user()

        response = self.client.post(
            "/api/login/",
            {"username": "existing-user", "password": "wrong-password"},
            format="json",
        )

        self.assertEqual(response.status_code, 401)
        self.assertNotIn(settings.ACCESS_TOKEN_COOKIE_NAME, response.cookies)

    def test_refresh_sets_new_access_cookie(self):
        user = create_user()
        refresh = RefreshToken.for_user(user)
        self.client.cookies[settings.REFRESH_TOKEN_COOKIE_NAME] = str(refresh)

        response = self.client.post("/api/token/refresh/", {}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertIn(settings.ACCESS_TOKEN_COOKIE_NAME, response.cookies)

    def test_logout_deletes_auth_cookies(self):
        user = create_user()
        authenticate_client(self.client, user)

        response = self.client.post("/api/logout/", {}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.cookies[settings.ACCESS_TOKEN_COOKIE_NAME].value, "")
        self.assertEqual(response.cookies[settings.REFRESH_TOKEN_COOKIE_NAME].value, "")
