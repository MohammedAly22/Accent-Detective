import os
import re
import tempfile
from typing import Tuple, Optional, Union, Dict, Any, List

import streamlit as st

import yt_dlp
import librosa

import whisper
from transformers import pipeline


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by replacing all characters that are not
    alphanumeric, dash, underscore, period, or space with an underscore.

    Args:
        - filename (str): The original filename to sanitize.

    Returns:
        - str: A sanitized filename safe for use in file paths.
    """

    return re.sub(r"[^\w\-_\. ]", "_", filename)


@st.cache_resource(show_spinner=False)
def load_models() -> Tuple[Any, Any]:
    """
    Load and cache the Whisper transcription model and Hugging Face audio
    classification pipeline.

    Returns:
        Tuple[Any, Any]: A tuple containing:
            - whisper_model (Any): The Whisper model loaded using `whisper.load_model`.
            - accent_classifier (Any): A Hugging Face audio classification pipeline
            instance for detecting English accents.
    """

    with st.spinner("🔄 Loading AI models... This may take a moment."):
        whisper_model = whisper.load_model("base")
        accent_classifier = pipeline(
            "audio-classification",
            model="dima806/english_accents_classification",
        )

    return whisper_model, accent_classifier


class AccentDetector:
    """
    A class to handle audio-based accent detection using Whisper for transcription
    and a Hugging Face model for accent classification.
    """

    def __init__(self):
        """
        Initializes the AccentDetector with the used models and predefined label mappings.
        """

        self.whisper_model, self.accent_classifier = load_models()
        self.label_mapping = {
            "us": "American",
            "canada": "Canadian",
            "australia": "Australian",
            "england": "British",
            "indian": "Indian",
        }

    def download_audio_from_url(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Downloads and converts audio from a YouTube URL into a .wav file.

        Args:
            - url (str): The YouTube video URL.

        Returns:
            - Tuple containing:
                - Path to the downloaded .wav file
                - Title of the video
        """

        # Create temp directory
        temp_dir = tempfile.mkdtemp()

        # Configure yt-dlp options
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(temp_dir, "%(title)s.%(ext)s"),
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "wav",
                    "preferredquality": "192K",
                }
            ],
            "quiet": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get("title", "audio")
                # Clean audio path
                safe_title = sanitize_filename(title)
                filename = os.path.join(temp_dir, f"{safe_title}.wav")

                # Ensure file exists
                if os.path.exists(filename):
                    return filename, title
                else:
                    # Fallback: search for any .wav file in the temp directory
                    for file in os.listdir(temp_dir):
                        if file.endswith(".wav"):
                            return os.path.join(temp_dir, file), title

        except Exception as e:
            st.error(f"❌ Error downloading audio: {str(e)}")
            return None, None

    def classify_accent(
        self, audio_path: str, rate_hz: int = 16000
    ) -> List[Dict[str, float]]:
        """
        Classifies the accent from a given audio file.

        Args:
            - audio_path (str): Path to the audio file.
            - rate_hz (int): Sample rate to resample audio to (default 16000 Hz),
            which is compatible with the `accent_classifier` model.

        Returns:
            - List of classification results with labels and scores.
        """

        audio, _ = librosa.load(audio_path, sr=rate_hz)
        return self.accent_classifier(audio)

    def process_video(self, url_or_file: Union[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Processes a video URL or uploaded file: extracts audio, transcribes it,
        and classifies the speaker's accent.

        Args:
            - url_or_file (Union[str, Any]): URL string of a YouTube video or an uploaded file object.

        Returns:
            - Dictionary containing results including:
                - title
                - transcript
                - language
                - accent scores
                - predicted accent
                - confidence score
        """

        results = {}

        try:
            # Step 1: Extract audio
            with st.spinner("🎵 Step 1: Extracting audio from video..."):
                # URL
                if isinstance(url_or_file, str):
                    audio_path, title = self.download_audio_from_url(url_or_file)
                    results["title"] = title
                # Uploaded file
                else:
                    temp_dir = tempfile.mkdtemp()
                    audio_path = os.path.join(temp_dir, url_or_file.name)
                    with open(audio_path, "wb") as f:
                        f.write(url_or_file.getvalue())
                    results["title"] = url_or_file.name

                # Display audio
                st.success("✅ Audio extraction completed successfully!")
                st.subheader("🔊 Audio preview", anchor=False)
                st.audio(audio_path)

                if not audio_path:
                    return None

            # Step 2: Transcribe audio using Whisper
            with st.spinner("🎯 Step 2: Transcribing audio with AI..."):
                result = self.whisper_model.transcribe(audio_path)
                transcript = result["text"]
                results["transcript"] = transcript
                results["language"] = result.get("language", "unknown")
                st.success("✅ Transcription completed successfully!")

            # Step 3: Classify the accent only if the detected language is English
            if results["language"] == "en":
                with st.spinner("🌍 Step 3: Detecting accent..."):
                    predicted_accents_scores = self.classify_accent(audio_path)
                    results["accent_scores"] = predicted_accents_scores
                    results["confidence"] = predicted_accents_scores[0]["score"] * 100
                    results["predicted_accent"] = self.label_mapping[
                        predicted_accents_scores[0]["label"]
                    ]

            # Step 4: Cleanup
            if os.path.exists(audio_path):
                os.remove(audio_path)

            return results

        except Exception as e:
            st.error(f"❌ Error processing video: {str(e)}")
            return None
