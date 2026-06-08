import json
import re
from json import JSONDecodeError

from django.conf import settings
from google import genai
from google.genai import errors

from .exceptions import QuizDataError, QuizProviderError


QUIZ_PROMPT_TEMPLATE = """
Based on the following transcript, generate a quiz in valid JSON format.

The quiz must follow this exact structure:

{{
  "title": "Create a concise quiz title based on the topic of the transcript.",
  "description": "Summarize the transcript in no more than 150 characters.",
  "questions": [
    {{
      "question_title": "The question goes here.",
      "question_options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "The correct answer from the above options"
    }}
  ]
}}

Requirements:
- Generate exactly 10 questions.
- Each question must have exactly 4 distinct answer options.
- Only one correct answer is allowed per question.
- The answer must be present in question_options.
- The output must be valid JSON and parsable with Python json.loads.
- Do not include explanations, comments, markdown, or text outside the JSON.

Transcript:
{transcript}
"""


def generate_quiz_data(transcript):
    """Generates and validates quiz JSON data with Gemini."""
    response_text = request_quiz_from_gemini(transcript)
    cleaned_text = clean_gemini_json_response(response_text)
    quiz_data = parse_quiz_json(cleaned_text)

    validate_quiz_data(quiz_data)
    return quiz_data


def request_quiz_from_gemini(transcript):
    """Sends the transcript to Gemini and returns the raw response text."""
    client = get_gemini_client()
    prompt = QUIZ_PROMPT_TEMPLATE.format(transcript=transcript)
    response = generate_gemini_response(client, prompt)

    return response.text


def generate_gemini_response(client, prompt):
    """Requests quiz content from Gemini."""
    try:
        return client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
        )
    except errors.APIError as exc:
        raise QuizProviderError("Gemini API request failed.") from exc


def get_gemini_client():
    """Returns a configured Gemini client."""
    if not settings.GEMINI_API_KEY:
        raise QuizProviderError("GEMINI_API_KEY is not configured.")

    return genai.Client(api_key=settings.GEMINI_API_KEY)


def clean_gemini_json_response(response_text):
    """Removes markdown code fences from Gemini JSON responses."""
    cleaned_text = response_text.strip()
    cleaned_text = re.sub(r"^```json\s*", "", cleaned_text)
    cleaned_text = re.sub(r"^```\s*", "", cleaned_text)
    cleaned_text = re.sub(r"\s*```$", "", cleaned_text)

    return cleaned_text.strip()


def parse_quiz_json(cleaned_text):
    """Parses Gemini output into a Python dictionary."""
    try:
        return json.loads(cleaned_text)
    except JSONDecodeError as exc:
        raise QuizDataError("Gemini returned invalid JSON.") from exc


def validate_quiz_data(quiz_data):
    """Validates the generated quiz structure."""
    if not isinstance(quiz_data, dict):
        raise QuizDataError("Gemini returned an invalid quiz object.")

    validate_quiz_root_fields(quiz_data)
    validate_questions(quiz_data["questions"])


def validate_quiz_root_fields(quiz_data):
    """Validates title, description, and questions fields."""
    required_fields = ["title", "description", "questions"]

    for field in required_fields:
        if field not in quiz_data:
            raise QuizDataError(f"Missing quiz field: {field}")


def validate_questions(questions):
    """Validates that exactly ten valid questions exist."""
    if not isinstance(questions, list):
        raise QuizDataError("Quiz questions must be a list.")

    if len(questions) != 10:
        raise QuizDataError("Quiz must contain exactly 10 questions.")

    for question in questions:
        validate_question(question)


def validate_question(question):
    """Validates one multiple-choice question."""
    required_fields = ["question_title", "question_options", "answer"]

    for field in required_fields:
        if field not in question:
            raise QuizDataError(f"Missing question field: {field}")

    validate_question_options(question)


def validate_question_options(question):
    """Validates answer options and correct answer."""
    options = question["question_options"]
    validate_options_list(options)
    validate_correct_answer(question, options)


def validate_options_list(options):
    """Validates the multiple-choice options list."""
    if not isinstance(options, list):
        raise QuizDataError("Question options must be a list.")

    if len(options) != 4:
        raise QuizDataError("Each question must contain 4 options.")

    if len(set(options)) != 4:
        raise QuizDataError("Question options must be distinct.")


def validate_correct_answer(question, options):
    """Validates that the answer is present in the options."""
    if question["answer"] not in options:
        raise QuizDataError("Answer must be part of question_options.")
