from django.db import transaction

from quiz_app.models import Question, Quiz

from .gemini_service import generate_quiz_data
from .transcript_service import transcribe_audio
from .youtube_service import download_audio_from_youtube


def create_quiz_from_youtube_url(user, url):
    """Creates a quiz from a YouTube URL."""
    audio_path = download_audio_from_youtube(url)

    try:
        transcript = transcribe_audio(audio_path)
        quiz_data = generate_quiz_data(transcript)
        return save_quiz(user, url, quiz_data)
    finally:
        delete_audio_file(audio_path)


@transaction.atomic
def save_quiz(user, url, quiz_data):
    """Stores a generated quiz and its questions."""
    quiz = Quiz.objects.create(
        user=user,
        title=quiz_data["title"],
        description=quiz_data["description"][:150],
        video_url=url,
    )

    create_questions(quiz, quiz_data["questions"])
    return quiz


def create_questions(quiz, questions):
    """Stores all generated questions for a quiz."""
    question_objects = [
        build_question(quiz, question)
        for question in questions
    ]

    Question.objects.bulk_create(question_objects)


def build_question(quiz, question):
    """Builds a question model instance."""
    return Question(
        quiz=quiz,
        question_title=question["question_title"],
        question_options=question["question_options"],
        answer=question["answer"],
    )


def delete_audio_file(audio_path):
    """Deletes a temporary audio file if it exists."""
    if audio_path and audio_path.exists():
        audio_path.unlink()