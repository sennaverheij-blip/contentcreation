"""Grok / xAI video generation client.

Generates image frames via the Grok Imagine API and stitches them into
a video with moviepy.
"""

import base64
from pathlib import Path

import requests
from moviepy import AudioFileClip, ImageSequenceClip


# Motion modifiers appended to each frame prompt for visual variety
MOTION_MODIFIERS = [
    "subtle zoom in",
    "slight pan left",
    "warm golden lighting shift",
    "shallow depth of field increase",
    "gentle lens flare",
    "subtle zoom out",
    "slight pan right",
    "cool blue lighting shift",
    "deep depth of field",
    "soft ambient glow",
]


class GrokVideoClient:
    """Client for generating video via the xAI Grok Imagine API.

    Generates 10 image frames with motion-variant prompts and stitches
    them into a video at 8 fps, with audio overlaid.
    """

    BASE_URL = "https://api.x.ai/v1"

    def __init__(self, api_key: str, base_image_path: str) -> None:
        self.api_key = api_key
        self.base_image_path = base_image_path

    def generate_image_frame(self, prompt: str, output_path: str) -> str:
        """Call Grok Imagine to generate one image frame.

        Decode b64_json response and save as PNG.

        Args:
            prompt: The image generation prompt.
            output_path: Where to save the generated PNG.

        Returns:
            The output_path of the saved image.

        Raises:
            RuntimeError: If the xAI API returns a non-200 response.
        """
        url = f"{self.BASE_URL}/images/generations"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "grok-2-image-1212",
            "prompt": prompt,
            "n": 1,
            "response_format": "b64_json",
        }

        resp = requests.post(url, json=payload, headers=headers, timeout=120)

        if resp.status_code != 200:
            raise RuntimeError(
                f"xAI image generation failed (HTTP {resp.status_code}): {resp.text}"
            )

        data = resp.json()
        b64_data = data["data"][0]["b64_json"]
        image_bytes = base64.b64decode(b64_data)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(image_bytes)

        return output_path

    def create_video(
        self,
        audio_path: str,
        script: str,
        setting: str,
        output_path: str = "output/video_raw.mp4",
    ) -> str:
        """Generate a video from image frames + audio.

        1. Build a base prompt from script + setting
        2. Generate 10 image frames via generate_image_frame(), each with
           a slight prompt variation to simulate camera motion
        3. Stitch frames into a video with moviepy ImageSequenceClip at 8fps
        4. Attach audio_path as the audio track, matched to audio duration
        5. Export to output_path at 30fps, codec libx264

        Args:
            audio_path: Path to the voiceover audio file.
            script: The spoken script text.
            setting: Scene/background description.
            output_path: Where to save the stitched video.

        Returns:
            The output_path of the generated video.

        Raises:
            RuntimeError: If any frame generation fails.
        """
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Extract first 8 words of script for the prompt
        script_words = " ".join(script.split()[:8])

        # Base prompt: setting + person speaking + cinematic quality + script excerpt
        base_prompt = (
            f"{setting}, a person speaking directly to camera, ultra-realistic, "
            f"cinematic lighting, 4K, sharp focus, {script_words}"
        )

        # Generate 10 frames, each with a different motion modifier
        frame_paths: list[str] = []
        for i in range(10):
            modifier = MOTION_MODIFIERS[i]
            prompt = f"{base_prompt}, {modifier}"
            frame_path = f"output/frame_{i:02d}.png"
            self.generate_image_frame(prompt, frame_path)
            frame_paths.append(frame_path)

        # Load audio to determine video duration
        audio = AudioFileClip(audio_path)

        # Stitch frames into video at 8fps, then match duration to audio
        clip = ImageSequenceClip(frame_paths, fps=8)
        clip = clip.set_audio(audio).set_duration(audio.duration)
        clip.write_videofile(
            output_path, codec="libx264", audio_codec="aac", fps=30
        )

        # Clean up temporary frame files
        clip.close()
        audio.close()
        for frame_path in frame_paths:
            Path(frame_path).unlink(missing_ok=True)

        return output_path
