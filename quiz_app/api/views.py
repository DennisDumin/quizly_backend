from rest_framework import status, viewsets
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from quiz_app.models import Quiz
from quiz_app.services.exceptions import QuizDownloadError, QuizServiceError
from quiz_app.services.quiz_generation_service import create_quiz_from_youtube_url

from .permissions import IsQuizOwner
from .serializers import (
    QuizCreateSerializer,
    QuizSerializer,
    QuizUpdateSerializer,
)


class QuizViewSet(viewsets.ModelViewSet):
    """Provides CRUD endpoints for user quizzes."""

    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated, IsQuizOwner]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        if self.action == "list":
            return Quiz.objects.filter(user=self.request.user)
        return Quiz.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return QuizCreateSerializer
        if self.action in ["partial_update", "update"]:
            return QuizUpdateSerializer
        return QuizSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        url = serializer.validated_data["url"]
        quiz = self.create_quiz(request.user, url)

        return Response(
            QuizSerializer(quiz).data,
            status=status.HTTP_201_CREATED,
        )

    def create_quiz(self, user, url):
        try:
            return create_quiz_from_youtube_url(user, url)
        except QuizDownloadError as exc:
            raise ValidationError({"url": str(exc)}) from exc
        except QuizServiceError as exc:
            raise APIException(str(exc)) from exc

    def partial_update(self, request, *args, **kwargs):
        quiz = self.get_object()
        serializer = self.get_serializer(quiz, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(QuizSerializer(quiz).data, status=status.HTTP_200_OK)