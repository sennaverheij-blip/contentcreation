"""Ayrshare social media posting client."""

from pathlib import Path

import requests


class AyrshareClient:
    """Client for posting videos to social media via the Ayrshare API."""

    BASE_URL = "https://app.ayrshare.com/api"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def upload_media(self, file_path: str) -> str:
        """Upload a video file to Ayrshare and return the hosted media URL.

        POST file to /media/upload as multipart/form-data.

        Args:
            file_path: Local path to the video file.

        Returns:
            The hosted URL string of the uploaded media.

        Raises:
            RuntimeError: If the upload fails.
        """
        url = f"{self.BASE_URL}/media/upload"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        with open(file_path, "rb") as f:
            files = {"file": (Path(file_path).name, f, "video/mp4")}
            resp = requests.post(url, files=files, headers=headers, timeout=120)

        if resp.status_code != 200:
            raise RuntimeError(
                f"Ayrshare media upload failed (HTTP {resp.status_code}): {resp.text}"
            )

        data = resp.json()
        media_url = data.get("url")
        if not media_url:
            raise RuntimeError(f"Ayrshare upload response missing URL: {data}")

        return media_url

    def post_video(
        self,
        video_path: str,
        caption: str,
        hashtags: list[str],
        platforms: list[str],
    ) -> dict:
        """Upload and post a video to the specified social platforms.

        1. Call upload_media() to get hosted URL
        2. POST to /post with payload
        3. Return response JSON

        Args:
            video_path: Local path to the final video file.
            caption: The post caption text.
            hashtags: List of hashtag strings (e.g. ["#AI", "#Video"]).
            platforms: Target platforms (e.g. ["instagram", "tiktok"]).

        Returns:
            The full Ayrshare API response as a dict.

        Raises:
            RuntimeError: If posting fails.
        """
        # Step 1: Upload the video to get a hosted URL
        media_url = self.upload_media(video_path)

        # Step 2: Create the post
        url = f"{self.BASE_URL}/post"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Combine caption and hashtags into the post text
        hashtag_str = " ".join(hashtags)
        post_text = f"{caption}\n\n{hashtag_str}"

        payload = {
            "post": post_text,
            "platforms": platforms,
            "mediaUrls": [media_url],
            "instagramOptions": {
                "reels": True,
                # shareReelsFeed: also show the Reel on the main profile grid
                "shareReelsFeed": True,
            },
            "tiktokOptions": {
                "privacy": "PUBLIC_TO_EVERYONE",
                "disableDuet": False,
                "disableComment": False,
            },
        }

        resp = requests.post(url, json=payload, headers=headers, timeout=60)

        if resp.status_code not in (200, 201):
            raise RuntimeError(
                f"Ayrshare post failed (HTTP {resp.status_code}): {resp.text}"
            )

        return resp.json()
