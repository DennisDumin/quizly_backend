import json
import re

from django.conf import settings
from google import genai


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
    quiz_data = json.loads(cleaned_text)

    validate_quiz_data(quiz_data)
    return quiz_data


def request_quiz_from_gemini(transcript):
    """Sends the transcript to Gemini and returns the raw response text."""
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    prompt = QUIZ_PROMPT_TEMPLATE.format(transcript=transcript)
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )

    return response.text


def clean_gemini_json_response(response_text):
    """Removes markdown code fences from Gemini JSON responses."""
    cleaned_text = response_text.strip()
    cleaned_text = re.sub(r"^```json\s*", "", cleaned_text)
    cleaned_text = re.sub(r"^```\s*", "", cleaned_text)
    cleaned_text = re.sub(r"\s*```$", "", cleaned_text)

    return cleaned_text.strip()


def validate_quiz_data(quiz_data):
    """Validates the generated quiz structure."""
    validate_quiz_root_fields(quiz_data)
    validate_questions(quiz_data["questions"])


def validate_quiz_root_fields(quiz_data):
    """Validates title, description, and questions fields."""
    required_fields = ["title", "description", "questions"]

    for field in required_fields:
        if field not in quiz_data:
            raise ValueError(f"Missing quiz field: {field}")


def validate_questions(questions):
    """Validates that exactly ten valid questions exist."""
    if len(questions) != 10:
        raise ValueError("Quiz must contain exactly 10 questions.")

    for question in questions:
        validate_question(question)


def validate_question(question):
    """Validates one multiple-choice question."""
    required_fields = ["question_title", "question_options", "answer"]

    for field in required_fields:
        if field not in question:
            raise ValueError(f"Missing question field: {field}")

    validate_question_options(question)


def validate_question_options(question):
    """Validates answer options and correct answer."""
    options = question["question_options"]

    if len(options) != 4:
        raise ValueError("Each question must contain 4 options.")

    if len(set(options)) != 4:
        raise ValueError("Question options must be distinct.")

    if question["answer"] not in options:
        raise ValueError("Answer must be part of question_options.")