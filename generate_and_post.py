#!/usr/bin/env python3
"""AI Clone Video System — main orchestration script.

Generates a voiceover, creates an AI avatar video, post-processes it,
and publishes to Instagram Reels and TikTok.

Usage:
    python generate_and_post.py --script "Your script here" --setting "Scene description"
"""

import os
import sys
from pathlib import Path

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from modules.ayrshare_client import AyrshareClient
from modules.elevenlabs_client import ElevenLabsClient
from modules.grok_video_client import GrokVideoClient
from modules.heygen_client import HeyGenClient
from modules.taisly_client import TaislyClient
from modules.video_processor import VideoProcessor

console = Console()


def validate_env_vars(required_vars: list[str]) -> None:
    """Check that all required environment variables are set."""
    missing = [var for var in required_vars if not os.environ.get(var)]
    if missing:
        console.print(
            f"[bold red]✗ Missing required environment variables:[/bold red] "
            f"{', '.join(missing)}"
        )
        console.print("  Please configure them in your .env file.")
        sys.exit(1)


@click.command()
@click.option("--script", required=True, help="The spoken script for the AI clone.")
@click.option(
    "--setting",
    required=True,
    help='Scene description, e.g. "futuristic lab with holograms".',
)
@click.option(
    "--caption",
    default=None,
    help="Social media caption. Auto-generated from script if omitted.",
)
@click.option(
    "--hashtags",
    default="#AI,#AIVideo,#ContentCreator",
    help="Hashtags as comma-separated string.",
)
@click.option(
    "--skip-post",
    is_flag=True,
    help="Generate video only, skip social posting.",
)
def main(
    script: str,
    setting: str,
    caption: str | None,
    hashtags: str,
    skip_post: bool,
) -> None:
    """AI Clone Video System — generate and post AI avatar videos."""

    # Load environment variables from .env
    load_dotenv()

    # Determine providers from env
    video_provider = os.environ.get("VIDEO_PROVIDER", "heygen").lower()
    social_provider = os.environ.get("SOCIAL_PROVIDER", "ayrshare").lower()
    target_platforms = [
        p.strip() for p in os.environ.get("TARGET_PLATFORMS", "instagram,tiktok").split(",")
    ]

    # Validate required env vars based on selected providers
    required = ["ELEVENLABS_API_KEY", "ELEVENLABS_VOICE_ID"]

    if video_provider == "heygen":
        required += ["HEYGEN_API_KEY", "HEYGEN_AVATAR_ID"]
    elif video_provider == "grok":
        required += ["GROK_API_KEY", "GROK_BASE_IMAGE_PATH"]
    else:
        console.print(f"[bold red]✗ VIDEO_PROVIDER must be 'heygen' or 'grok', got '{video_provider}'[/bold red]")
        sys.exit(1)

    if not skip_post:
        if social_provider == "ayrshare":
            required += ["AYRSHARE_API_KEY"]
        elif social_provider == "taisly":
            required += ["TAISLY_API_KEY", "TAISLY_USER_ID"]
        else:
            console.print(f"[bold red]✗ SOCIAL_PROVIDER must be 'ayrshare' or 'taisly', got '{social_provider}'[/bold red]")
            sys.exit(1)

    validate_env_vars(required)

    # Ensure output directory exists
    Path("output").mkdir(parents=True, exist_ok=True)

    # Display startup panel
    console.print(
        Panel(
            f"[bold green]AI Clone Video System Starting[/bold green]\n"
            f"Video Provider : {video_provider}\n"
            f"Social Provider: {social_provider}\n"
            f"Platforms      : {', '.join(target_platforms)}",
            expand=False,
        )
    )

    audio_path = None
    video_raw_path = None
    video_final_path = None
    post_result = None

    # ── Step A: Generate audio via ElevenLabs ──
    try:
        console.print("\n[1/4] Generating audio via ElevenLabs...", end="  ")
        el_client = ElevenLabsClient(
            api_key=os.environ["ELEVENLABS_API_KEY"],
            voice_id=os.environ["ELEVENLABS_VOICE_ID"],
        )
        audio_path = el_client.generate_audio(script)
        console.print(f"[green]✓[/green] {audio_path}")
    except Exception as e:
        console.print(f"[bold red]✗ Error:[/bold red] {e}")
        sys.exit(1)

    # ── Step B: Generate video ──
    try:
        console.print(f"[2/4] Generating video via {video_provider.title()}...", end="  ")
        if video_provider == "heygen":
            video_client = HeyGenClient(
                api_key=os.environ["HEYGEN_API_KEY"],
                avatar_id=os.environ["HEYGEN_AVATAR_ID"],
            )
        else:
            video_client = GrokVideoClient(
                api_key=os.environ["GROK_API_KEY"],
                base_image_path=os.environ["GROK_BASE_IMAGE_PATH"],
            )
        video_raw_path = video_client.create_video(audio_path, script, setting)
        console.print(f"[green]✓[/green] {video_raw_path}")
    except Exception as e:
        console.print(f"[bold red]✗ Error:[/bold red] {e}")
        sys.exit(1)

    # ── Step C: Post-process video ──
    try:
        console.print("[3/4] Processing video (9:16, trim)...", end="  ")
        processor = VideoProcessor()
        video_final_path = processor.process(video_raw_path, audio_path)
        console.print(f"[green]✓[/green] {video_final_path}")
    except Exception as e:
        console.print(f"[bold red]✗ Error:[/bold red] {e}")
        sys.exit(1)

    # ── Step D: Post to social media ──
    if skip_post:
        console.print("[4/4] Posting skipped (--skip-post flag).")
    else:
        try:
            console.print(
                f"[4/4] Posting to {' + '.join(p.title() for p in target_platforms)}...",
                end="  ",
            )

            # Parse hashtags from comma-separated CLI arg
            hashtag_list = [h.strip() for h in hashtags.split(",") if h.strip()]

            # Auto-generate caption from first sentence if not provided
            if caption is None:
                first_sentence = script.split(".")[0].strip()
                caption = first_sentence + "." if first_sentence else script[:100]

            if social_provider == "ayrshare":
                social_client = AyrshareClient(api_key=os.environ["AYRSHARE_API_KEY"])
            else:
                social_client = TaislyClient(
                    api_key=os.environ["TAISLY_API_KEY"],
                    user_id=os.environ["TAISLY_USER_ID"],
                )

            post_result = social_client.post_video(
                video_path=video_final_path,
                caption=caption,
                hashtags=hashtag_list,
                platforms=target_platforms,
            )
            console.print(f"[green]✓[/green] Post IDs: {post_result}")
        except Exception as e:
            console.print(f"[bold red]✗ Error:[/bold red] {e}")
            sys.exit(1)

    # ── Summary ──
    console.print()
    table = Table(title="Summary")
    table.add_column("Output", style="cyan")
    table.add_column("Path / Value", style="green")
    table.add_row("Audio", audio_path or "—")
    table.add_row("Raw Video", video_raw_path or "—")
    table.add_row("Final Video", video_final_path or "—")
    table.add_row("Post Result", str(post_result) if post_result else "Skipped")
    console.print(table)

    console.print("\n[bold green]✓ Done![/bold green] Video posted successfully.")


if __name__ == "__main__":
    main()
