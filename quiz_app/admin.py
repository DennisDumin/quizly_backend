from django.contrib import admin

from .models import Question, Quiz


class QuestionInline(admin.TabularInline):
    """Displays quiz questions inside the quiz admin page."""

    model = Question
    extra = 0


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """Configures the quiz admin page."""

    list_display = ["id", "title", "user", "created_at"]
    search_fields = ["title", "description", "video_url"]
    list_filter = ["created_at", "updated_at"]
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Configures the question admin page."""

    list_display = ["id", "question_title", "quiz", "created_at"]
    search_fields = ["question_title", "answer"]
    list_filter = ["created_at", "updated_at"]