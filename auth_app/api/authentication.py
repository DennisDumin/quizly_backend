from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    """Authenticates users with a JWT stored in an HTTP-only cookie."""

    def authenticate(self, request):
        access_token = request.COOKIES.get(settings.ACCESS_TOKEN_COOKIE_NAME)

        if not access_token:
            return None

        validated_token = self.get_validated_token(access_token)
        user = self.get_user(validated_token)

        return user, validated_token