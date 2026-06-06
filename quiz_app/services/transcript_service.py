import whisper


def transcribe_audio(audio_path):
    """Transcribes an audio file into plain text."""
    model = whisper.load_model("base")
    result = model.transcribe(str(audio_path))

    return clean_transcript(result.get("text", ""))


def clean_transcript(transcript):
    """Removes unnecessary whitespace from a transcript."""
    return " ".join(transcript.split())