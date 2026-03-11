"""Grok / xAI video generation client."""

import time
from pathlib import Path

import requests

# TODO: Update endpoint when xAI releases stable video API


class GrokVideoClient:
    """Client for generating video via the xAI Grok Imagine API.

    Currently uses the xAI image generation endpoint. When xAI releases a
    dedicated video generation API, this client should be updated accordingly.
    """

    BASE_URL = "https://api.x.ai/v1"

    def __init__(self, api_key: str, base_image_path: str) -> None:
        self.api_key = api_key
        self.base_image_path = base_image_path

    def create_video(self, audio_path: str, script: str, setting: str) -> str:
        """Generate a video from the base image, script, and scene setting.

        If xAI supports direct video generation, uses that endpoint. Otherwise
        generates a sequence of images and stitches them together with the
        provided audio using moviepy.

        Args:
            audio_path: Path to the voiceover audio file.
            script: The spoken script text.
            setting: Scene/background description.

        Returns:
            Path to the generated raw video file.

        Raises:
            RuntimeError: If the xAI API returns an error.
        """
        # Try direct video generation first
        # TODO: Update endpoint when xAI releases stable video API
        video_path = self._try_direct_video(script, setting)
        if video_path:
            return video_path

        # Fallback: generate images and stitch into a video with audio
        return self._generate_image_sequence_video(audio_path, script, setting)

    def _try_direct_video(self, script: str, setting: str) -> str | None:
        """Attempt to use xAI's video generation endpoint if available.

        Returns:
            Path to the video file if successful, None if endpoint unavailable.
        """
        # TODO: Update endpoint when xAI releases stable video API
        url = f"{self.BASE_URL}/video/generations"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Use a short excerpt of the script for the video prompt
        script_excerpt = script[:200] if len(script) > 200 else script

        payload = {
            "prompt": f"{setting}. {script_excerpt}",
            "n": 1,
            "size": "1080x1920",
        }

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=120)
            if resp.status_code == 404:
                # Video endpoint not available yet
                return None
            if resp.status_code != 200:
                raise RuntimeError(
                    f"xAI video generation failed (HTTP {resp.status_code}): {resp.text}"
                )

            data = resp.json()
            video_url = data.get("data", [{}])[0].get("url")
            if video_url:
                return self._download_file(video_url, "output/video_raw.mp4")
            return None
        except requests.exceptions.ConnectionError:
            # Endpoint doesn't exist yet
            return None

    def _generate_image_sequence_video(
        self, audio_path: str, script: str, setting: str
    ) -> str:
        """Generate images via xAI and stitch them into a video with moviepy.

        Creates a slideshow-style video from generated images, overlaid with
        the provided audio track.
        """
        from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips

        # Generate a set of images to create a slideshow video
        num_frames = 5
        image_paths: list[str] = []

        for i in range(num_frames):
            # Vary the prompt slightly for each frame
            prompt_suffix = f"Frame {i + 1}: " + (
                script[i * len(script) // num_frames : (i + 1) * len(script) // num_frames]
            )
            img_path = self._generate_image(f"{setting}. {prompt_suffix}", i)
            image_paths.append(img_path)

        # Get audio duration to calculate per-image display time
        audio_clip = AudioFileClip(audio_path)
        duration_per_image = audio_clip.duration / len(image_paths)

        # Build video from image sequence
        clips = []
        for img_path in image_paths:
            clip = ImageClip(img_path).set_duration(duration_per_image).resize((1080, 1920))
            clips.append(clip)

        video = concatenate_videoclips(clips, method="compose")
        video = video.set_audio(audio_clip)

        output_path = "output/video_raw.mp4"
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        video.write_videofile(
            output_path, codec="libx264", audio_codec="aac", fps=30
        )

        # Clean up temporary image files
        for img_path in image_paths:
            Path(img_path).unlink(missing_ok=True)

        return output_path

    def _generate_image(self, prompt: str, index: int) -> str:
        """Generate a single image via the xAI image generation API."""
        url = f"{self.BASE_URL}/images/generations"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "prompt": prompt,
            "n": 1,
            "size": "1080x1920",
        }

        resp = requests.post(url, json=payload, headers=headers, timeout=120)
        if resp.status_code != 200:
            raise RuntimeError(
                f"xAI image generation failed (HTTP {resp.status_code}): {resp.text}"
            )

        data = resp.json()
        image_url = data.get("data", [{}])[0].get("url")
        if not image_url:
            raise RuntimeError(f"xAI response missing image URL: {data}")

        return self._download_file(image_url, f"output/temp_frame_{index}.png")

    def _download_file(self, url: str, output_path: str) -> str:
        """Download a file from a URL to a local path."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        resp = requests.get(url, stream=True, timeout=120)
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to download from {url} (HTTP {resp.status_code})")

        with open(output_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        return output_path
