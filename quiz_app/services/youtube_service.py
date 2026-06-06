from pathlib import Path

from django.conf import settings
from yt_dlp import YoutubeDL


def get_download_dir():
    """Returns the local directory for downloaded audio files."""
    download_dir = Path(settings.MEDIA_ROOT) / "downloads"
    download_dir.mkdir(parents=True, exist_ok=True)
    return download_dir


def get_audio_postprocessor():
    """Returns the FFmpeg audio extraction configuration."""
    return {
        "key": "FFmpegExtractAudio",
        "preferredcodec": "mp3",
        "preferredquality": "192",
    }


def get_ydl_options(download_dir):
    """Returns yt-dlp options for audio extraction."""
    return {
        "format": "bestaudio/best",
        "outtmpl": str(download_dir / "%(id)s.%(ext)s"),
        "postprocessors": [get_audio_postprocessor()],
        "quiet": True,
        "noplaylist": True,
    }


def download_audio_from_youtube(url):
    """Downloads a YouTube video as an MP3 audio file."""
    download_dir = get_download_dir()

    with YoutubeDL(get_ydl_options(download_dir)) as ydl:
        info = ydl.extract_info(url, download=True)

    return get_audio_path(download_dir, info)


def get_audio_path(download_dir, info):
    """Builds the final MP3 file path from yt-dlp video info."""
    video_id = info.get("id")
    audio_path = download_dir / f"{video_id}.mp3"

    if not audio_path.exists():
        raise FileNotFoundError("Audio file could not be created.")

    return audio_path