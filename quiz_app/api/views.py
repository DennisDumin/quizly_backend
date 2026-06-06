from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from quiz_app.models import Quiz

from .permissions import IsQuizOwner
from .serializers import (
    QuizCreateSerializer,
    QuizSerializer,
    QuizUpdateSerializer,
)


class QuizViewSet(viewsets.ModelViewSet):
    """Provides CRUD endpoints for user quizzes."""

    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated, IsQuizOwner]

    def get_queryset(self):
        return Quiz.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return QuizCreateSerializer
        if self.action in ["partial_update", "update"]:
            return QuizUpdateSerializer
        return QuizSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response(
            {"detail": "Quiz generation will be added next."},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )

    def partial_update(self, request, *args, **kwargs):
        quiz = self.get_object()
        serializer = self.get_serializer(quiz, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(QuizSerializer(quiz).data, status=status.HTTP_200_OK)