from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class UserSerializer(serializers.ModelSerializer):
    """Serializes public user data."""

    class Meta:
        model = User
        fields = ["id", "username", "email"]


class RegisterSerializer(serializers.Serializer):
    """Validates data for user registration."""

    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)
    confirmed_password = serializers.CharField(write_only=True)
    email = serializers.EmailField()

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["confirmed_password"]:
            raise serializers.ValidationError("Passwords do not match.")
        return attrs

    def create(self, validated_data):
        validated_data.pop("confirmed_password")
        return User.objects.create_user(**validated_data)


class LoginSerializer(TokenObtainPairSerializer):
    """Validates credentials and prepares the JWT cookie response data."""

    default_error_messages = {"no_active_account": "Invalid credentials."}

    def validate(self, attrs):
        token_data = super().validate(attrs)
        self.access_token = token_data["access"]
        self.refresh_token = token_data["refresh"]

        return {
            "detail": "Login successfully!",
            "user": UserSerializer(self.user).data,
        }
