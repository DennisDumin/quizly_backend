class QuizServiceError(Exception):
    """Base error for the quiz generation pipeline."""


class QuizDownloadError(QuizServiceError):
    """Raised when audio cannot be downloaded from YouTube."""


class QuizProviderError(QuizServiceError):
    """Raised when an external AI provider cannot return quiz data."""


class QuizDataError(QuizServiceError):
    """Raised when generated quiz data has an invalid structure."""
