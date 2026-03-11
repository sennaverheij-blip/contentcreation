"""Taisly social media posting client."""

from pathlib import Path

import requests

# TODO: Verify exact Taisly endpoint URLs from their API docs


class TaislyClient:
    """Client for posting videos to social media via the Taisly API.

    Note: Taisly endpoint URLs and request formats should be verified against
    their official API documentation, as they may change.
    """

    # TODO: Verify exact Taisly base URL from their API docs
    BASE_URL = "https://api.taisly.com/v1"

    def __init__(self, api_key: str, user_id: str) -> None:
        self.api_key = api_key
        self.user_id = user_id

    def _upload_video(self, video_path: str) -> str:
        """Upload a video file to Taisly's media storage.

        Args:
            video_path: Local path to the video file.

        Returns:
            The media ID or URL of the uploaded video.

        Raises:
            RuntimeError: If the upload fails.
        """
        # TODO: Verify exact Taisly upload endpoint from their API docs
        url = f"{self.BASE_URL}/media/upload"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-User-Id": self.user_id,
        }

        with open(video_path, "rb") as f:
            files = {"file": (Path(video_path).name, f, "video/mp4")}
            resp = requests.post(url, files=files, headers=headers, timeout=120)

        if resp.status_code not in (200, 201):
            raise RuntimeError(
                f"Taisly media upload failed (HTTP {resp.status_code}): {resp.text}"
            )

        data = resp.json()
        media_id = data.get("media_id") or data.get("url")
        if not media_id:
            raise RuntimeError(f"Taisly upload response missing media identifier: {data}")

        return media_id

    def post_video(
        self,
        video_path: str,
        caption: str,
        hashtags: list[str],
        platforms: list[str],
    ) -> dict:
        """Upload and post a video to social platforms via Taisly.

        Args:
            video_path: Local path to the final video file.
            caption: The post caption text.
            hashtags: List of hashtag strings.
            platforms: Target platforms (e.g. ["instagram", "tiktok"]).

        Returns:
            The Taisly API response as a dict.

        Raises:
            RuntimeError: If posting fails.
        """
        # Step 1: Upload the video
        media_id = self._upload_video(video_path)

        # Step 2: Create the post
        # TODO: Verify exact Taisly post endpoint from their API docs
        url = f"{self.BASE_URL}/posts"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-User-Id": self.user_id,
            "Content-Type": "application/json",
        }

        payload = {
            "media_id": media_id,
            "caption": caption,
            "hashtags": hashtags,
            "platforms": platforms,
            "options": {
                "instagram": {"type": "reels"},
                "tiktok": {"privacy": "public"},
            },
        }

        resp = requests.post(url, json=payload, headers=headers, timeout=60)

        if resp.status_code not in (200, 201):
            raise RuntimeError(
                f"Taisly post failed (HTTP {resp.status_code}): {resp.text}"
            )

        return resp.json()
