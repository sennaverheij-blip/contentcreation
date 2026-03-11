"""HeyGen AI avatar video generation client."""

import base64
import time
from pathlib import Path

import requests


class HeyGenClient:
    """Client for generating avatar videos via the HeyGen API."""

    BASE_URL = "https://api.heygen.com"
    # Maximum time to wait for video generation before timing out
    MAX_POLL_SECONDS = 600  # 10 minutes
    POLL_INTERVAL = 10  # seconds between status checks

    def __init__(self, api_key: str, avatar_id: str) -> None:
        self.api_key = api_key
        self.avatar_id = avatar_id

    def _upload_audio_base64(self, audio_path: str) -> str:
        """Encode a local audio file as a base64 data URI.

        HeyGen's v2 API accepts audio as a URL. Since ElevenLabs returns a
        local file, we upload it via HeyGen's asset upload endpoint. If that
        is unavailable, we fall back to embedding the audio as a base64 data
        URI (supported by some HeyGen API versions).
        """
        # Try uploading via HeyGen's asset upload endpoint first
        upload_url = f"{self.BASE_URL}/v1/asset"
        with open(audio_path, "rb") as f:
            files = {"file": (Path(audio_path).name, f, "audio/mpeg")}
            headers = {"X-Api-Key": self.api_key}
            resp = requests.post(upload_url, files=files, headers=headers, timeout=60)

        if resp.status_code == 200:
            data = resp.json()
            # The asset upload returns a URL we can use directly
            if "data" in data and "url" in data["data"]:
                return data["data"]["url"]

        # Fallback: use base64 data URI encoding
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()
        b64 = base64.b64encode(audio_bytes).decode("utf-8")
        return f"data:audio/mpeg;base64,{b64}"

    def create_video(self, audio_path: str, script: str, setting: str) -> str:
        """Generate an avatar video with the given audio and scene setting.

        Args:
            audio_path: Path to the local audio file (MP3).
            script: The spoken script (used for lip-sync alignment).
            setting: Scene description for background image keywords.

        Returns:
            Path to the downloaded raw video file.

        Raises:
            RuntimeError: If video generation fails or times out.
        """
        audio_url = self._upload_audio_base64(audio_path)

        # Convert setting description into URL-safe keywords for Unsplash
        setting_keywords = setting.replace(" ", ",")

        url = f"{self.BASE_URL}/v2/video/generate"
        headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json",
        }

        payload = {
            "video_inputs": [
                {
                    "character": {
                        "type": "avatar",
                        "avatar_id": self.avatar_id,
                        "avatar_style": "normal",
                    },
                    "voice": {
                        "type": "audio",
                        "audio_url": audio_url,
                    },
                    "background": {
                        "type": "image",
                        "url": f"https://source.unsplash.com/1920x1080/?{setting_keywords}",
                    },
                }
            ],
            "dimension": {"width": 1080, "height": 1920},
            "aspect_ratio": "9:16",
        }

        response = requests.post(url, json=payload, headers=headers, timeout=60)

        if response.status_code != 200:
            raise RuntimeError(
                f"HeyGen video creation failed (HTTP {response.status_code}): {response.text}"
            )

        resp_data = response.json()
        video_id = resp_data.get("data", {}).get("video_id")
        if not video_id:
            raise RuntimeError(f"HeyGen response missing video_id: {resp_data}")

        # Poll for completion
        return self._poll_and_download(video_id)

    def _poll_and_download(self, video_id: str) -> str:
        """Poll HeyGen for video status and download when complete."""
        status_url = f"{self.BASE_URL}/v1/video_status.get"
        headers = {"X-Api-Key": self.api_key}
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time
            if elapsed > self.MAX_POLL_SECONDS:
                raise RuntimeError(
                    f"HeyGen video generation timed out after {self.MAX_POLL_SECONDS}s "
                    f"(video_id: {video_id})"
                )

            resp = requests.get(
                status_url, params={"video_id": video_id}, headers=headers, timeout=30
            )

            if resp.status_code != 200:
                raise RuntimeError(
                    f"HeyGen status check failed (HTTP {resp.status_code}): {resp.text}"
                )

            data = resp.json().get("data", {})
            status = data.get("status")

            if status == "completed":
                video_url = data.get("video_url")
                if not video_url:
                    raise RuntimeError(f"HeyGen completed but no video_url in response: {data}")
                return self._download_video(video_url)

            if status == "failed":
                error = data.get("error", "Unknown error")
                raise RuntimeError(f"HeyGen video generation failed: {error}")

            # Still processing — wait before next poll
            time.sleep(self.POLL_INTERVAL)

    def _download_video(self, video_url: str) -> str:
        """Download the completed video to a local file."""
        output_path = "output/video_raw.mp4"
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        resp = requests.get(video_url, stream=True, timeout=120)
        if resp.status_code != 200:
            raise RuntimeError(
                f"Failed to download HeyGen video (HTTP {resp.status_code})"
            )

        with open(output_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        return output_path
