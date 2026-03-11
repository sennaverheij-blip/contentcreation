"""Video post-processing module for format normalization."""

from pathlib import Path

from moviepy.editor import AudioFileClip, VideoFileClip


class VideoProcessor:
    """Processes raw video to meet social media platform requirements.

    Ensures output is 9:16 aspect ratio (1080x1920), correct codec,
    and within platform duration limits.
    """

    # Platform duration limits in seconds
    INSTAGRAM_REELS_MAX = 90
    TIKTOK_MAX = 180
    # Use the stricter limit to ensure compatibility with both platforms
    SAFE_MAX_DURATION = 89  # 1s under Instagram's 90s limit

    TARGET_WIDTH = 1080
    TARGET_HEIGHT = 1920

    def process(
        self,
        video_path: str,
        audio_path: str,
        output_path: str = "output/video_final.mp4",
    ) -> str:
        """Process video to meet platform specs (9:16, duration, codecs).

        Args:
            video_path: Path to the raw input video.
            audio_path: Path to the audio file to overlay.
            output_path: Where to save the processed video.

        Returns:
            The output file path.
        """
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        video = VideoFileClip(video_path)
        audio = AudioFileClip(audio_path)

        # Replace video audio with the ElevenLabs voiceover
        video = video.set_audio(audio)

        # Resize to 9:16 (1080x1920) if not already the correct dimensions
        if video.w != self.TARGET_WIDTH or video.h != self.TARGET_HEIGHT:
            video = video.resize((self.TARGET_WIDTH, self.TARGET_HEIGHT))

        # Trim to safe duration if the video exceeds platform limits
        if video.duration > self.SAFE_MAX_DURATION:
            video = video.subclip(0, self.SAFE_MAX_DURATION)

        video.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            fps=30,
        )

        # Clean up file handles
        video.close()
        audio.close()

        return output_path
