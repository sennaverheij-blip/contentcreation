"""ElevenLabs Professional Voice Cloning client."""

import os
from pathlib import Path

import requests


class ElevenLabsClient:
    """Client for generating voiceover audio via the ElevenLabs TTS API."""

    BASE_URL = "https://api.elevenlabs.io/v1"

    def __init__(self, api_key: str, voice_id: str) -> None:
        self.api_key = api_key
        self.voice_id = voice_id

    def generate_audio(self, script: str, output_path: str = "output/audio.mp3") -> str:
        """Generate speech audio from a script using the cloned voice.

        Args:
            script: The text to convert to speech.
            output_path: Where to save the resulting MP3 file.

        Returns:
            The path to the saved audio file.

        Raises:
            RuntimeError: If the ElevenLabs API returns a non-200 response.
        """
        url = f"{self.BASE_URL}/text-to-speech/{self.voice_id}"

        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
        }

        payload = {
            "text": script,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                # similarity_boost controls how closely the output matches the cloned voice
                "similarity_boost": 0.85,
            },
        }

        response = requests.post(url, json=payload, headers=headers, stream=True, timeout=120)

        if response.status_code != 200:
            raise RuntimeError(
                f"ElevenLabs API error (HTTP {response.status_code}): {response.text}"
            )

        # Ensure the output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=4096):
                if chunk:
                    f.write(chunk)

        return output_path
