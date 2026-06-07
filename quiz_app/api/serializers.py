from urllib.parse import urlparse

from rest_framework import serializers

from quiz_app.models import Question, Quiz


YOUTUBE_HOSTS = {"youtube.com", "m.youtube.com", "www.youtube.com", "youtu.be"}


class QuestionSerializer(serializers.ModelSerializer):
    """Serializes quiz questions."""

    class Meta:
        model = Question
        fields = [
            "id",
            "question_title",
            "question_options",
            "answer",
            "created_at",
            "updated_at",
        ]


class QuizSerializer(serializers.ModelSerializer):
    """Serializes quizzes with their questions."""

    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = [
            "id",
            "title",
            "description",
            "created_at",
            "updated_at",
            "video_url",
            "questions",
        ]


class QuizUpdateSerializer(serializers.ModelSerializer):
    """Validates partial quiz updates."""

    class Meta:
        model = Quiz
        fields = ["title", "description"]


class QuizCreateSerializer(serializers.Serializer):
    """Validates the YouTube URL used to generate a quiz."""

    url = serializers.URLField(max_length=500)

    def validate_url(self, value):
        parsed_url = urlparse(value)
        host = parsed_url.netloc.lower()

        if host not in YOUTUBE_HOSTS:
            raise serializers.ValidationError("Enter a valid YouTube URL.")

        return value
