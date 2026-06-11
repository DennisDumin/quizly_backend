from django.conf import settings
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import LoginSerializer, RegisterSerializer


def set_access_cookie(response, access_token):
    """Stores the access token in an HTTP-only cookie."""
    response.set_cookie(
        key=settings.ACCESS_TOKEN_COOKIE_NAME,
        value=str(access_token),
        httponly=settings.COOKIE_HTTP_ONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=60 * 30,
    )


def set_refresh_cookie(response, refresh_token):
    """Stores the refresh token in an HTTP-only cookie."""
    response.set_cookie(
        key=settings.REFRESH_TOKEN_COOKIE_NAME,
        value=str(refresh_token),
        httponly=settings.COOKIE_HTTP_ONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=60 * 60 * 24 * 7,
    )


def delete_auth_cookies(response):
    """Deletes all authentication cookies."""
    response.delete_cookie(settings.ACCESS_TOKEN_COOKIE_NAME)
    response.delete_cookie(settings.REFRESH_TOKEN_COOKIE_NAME)


def blacklist_refresh_token(request):
    """Invalidates the refresh token cookie if blacklisting is available."""
    token = request.COOKIES.get(settings.REFRESH_TOKEN_COOKIE_NAME)

    if not token:
        return

    try:
        RefreshToken(token).blacklist()
    except TokenError:
        return


def raise_authentication_error(message="Invalid credentials."):
    """Raises a standardized authentication error."""
    raise AuthenticationFailed(message)


class RegisterView(APIView):
    """Creates a new user account."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"detail": "User created successfully!"},
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    """Authenticates a user with SimpleJWT and sets JWT cookies."""

    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        """Validates credentials and returns user data with auth cookies."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        response = Response(serializer.validated_data, status=status.HTTP_200_OK)

        set_access_cookie(response, serializer.access_token)
        set_refresh_cookie(response, serializer.refresh_token)

        return response


class LogoutView(APIView):
    """Logs out the user by deleting authentication cookies."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        blacklist_refresh_token(request)
        response = Response(
            {
                "detail": (
                    "Log-Out successfully! All Tokens will be deleted. "
                    "Refresh token is now invalid."
                )
            },
            status=status.HTTP_200_OK,
        )
        delete_auth_cookies(response)
        return response


class RefreshTokenView(APIView):
    """Creates a new access token from the refresh token cookie."""

    permission_classes = [AllowAny]

    def post(self, request):
        refresh = self.get_refresh_token(request)
        response = Response(
            {"detail": "Token refreshed"},
            status=status.HTTP_200_OK,
        )

        set_access_cookie(response, refresh.access_token)

        return response

    def get_refresh_token(self, request):
        token = request.COOKIES.get(settings.REFRESH_TOKEN_COOKIE_NAME)

        if not token:
            raise_authentication_error("Refresh Token missing.")

        try:
            return RefreshToken(token)
        except Exception:
            raise_authentication_error("Refresh Token invalid.")
