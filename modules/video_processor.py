"""Video post-processing module for format normalization."""

from pathlib import Path

from moviepy import VideoFileClip


class VideoProcessor:
    """Processes raw video to meet social media platform requirements.

    Ensures output is 9:16 aspect ratio (1080x1920), correct codec,
    and within platform duration limits.
    """

    MAX_DURATION_SECONDS: int = 89  # Instagram Reels hard cap is 90s
    TARGET_WIDTH: int = 1080
    TARGET_HEIGHT: int = 1920
    TARGET_RATIO: float = 9 / 16  # 0.5625

    def process(
        self,
        video_path: str,
        output_path: str = "output/video_final.mp4",
    ) -> str:
        """Process video: crop/resize to 9:16, trim duration, re-encode.

        1. Load with moviepy VideoFileClip
        2. Trim to MAX_DURATION_SECONDS if needed
        3. Crop/resize to 1080x1920 (9:16):
           - Wider than 9:16 -> crop sides equally
           - Taller than 9:16 -> crop top/bottom equally
        4. Export: codec=libx264, audio_codec=aac, fps=30, bitrate="5000k"

        Args:
            video_path: Path to the raw input video.
            output_path: Where to save the processed video.

        Returns:
            The output file path.
        """
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        video = VideoFileClip(video_path)

        # Trim to safe duration if the video exceeds platform limits
        if video.duration > self.MAX_DURATION_SECONDS:
            video = video.subclip(0, self.MAX_DURATION_SECONDS)

        # Crop to 9:16 aspect ratio before resizing
        current_ratio = video.w / video.h

        if current_ratio > self.TARGET_RATIO:
            # Video is wider than 9:16 — crop sides equally
            new_width = int(video.h * self.TARGET_RATIO)
            x_offset = (video.w - new_width) // 2
            video = video.crop(x1=x_offset, x2=x_offset + new_width)
        elif current_ratio < self.TARGET_RATIO:
            # Video is taller than 9:16 — crop top/bottom equally
            new_height = int(video.w / self.TARGET_RATIO)
            y_offset = (video.h - new_height) // 2
            video = video.crop(y1=y_offset, y2=y_offset + new_height)

        # Resize to exact target dimensions
        video = video.resize((self.TARGET_WIDTH, self.TARGET_HEIGHT))

        video.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            fps=30,
            bitrate="5000k",
        )

        video.close()

        return output_path
