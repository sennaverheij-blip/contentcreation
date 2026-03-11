#!/usr/bin/env python3
"""AI Clone Video System — generates a Grok AI video and posts to Instagram + TikTok."""

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
from modules.video_processor import VideoProcessor

console = Console()

REQUIRED_ENV_VARS = [
    "ELEVENLABS_API_KEY",
    "ELEVENLABS_VOICE_ID",
    "GROK_API_KEY",
    "GROK_BASE_IMAGE_PATH",
    "AYRSHARE_API_KEY",
    "TARGET_PLATFORMS",
]


def validate_env() -> None:
    """Check that all required environment variables are set."""
    missing = [v for v in REQUIRED_ENV_VARS if not os.getenv(v)]
    if missing:
        console.print("[bold red]Missing environment variables:[/bold red]")
        for v in missing:
            console.print(f"  \u2022 {v}")
        console.print("[dim]Copy .env.template \u2192 .env and fill in your keys.[/dim]")
        sys.exit(1)


@click.command()
@click.option("--script", required=True, help="The spoken script for the AI clone.")
@click.option("--setting", required=True, help='Scene description, e.g. "futuristic lab with holograms".')
@click.option("--caption", default=None, help="Social media caption. Auto-generated from script if omitted.")
@click.option("--hashtags", default="#AI,#AIVideo,#ContentCreator", help="Hashtags as comma-separated string.")
@click.option("--skip-post", is_flag=True, help="Generate video only, skip social posting.")
def main(script: str, setting: str, caption: str | None, hashtags: str, skip_post: bool) -> None:
    """AI Clone Video System — generate and post AI avatar videos."""
    load_dotenv()
    validate_env()
    Path("output").mkdir(exist_ok=True)

    platforms = [p.strip() for p in os.environ["TARGET_PLATFORMS"].split(",")]
    hashtag_list = [h.strip() for h in hashtags.split(",")]
    final_caption = caption or script.split(".")[0].strip()

    console.print(Panel.fit(
        "[bold green]AI Clone Video System[/bold green]\n"
        f"[dim]Video :[/dim] [cyan]Grok / xAI[/cyan]   "
        f"[dim]Social:[/dim] [cyan]Ayrshare[/cyan]   "
        f"[dim]Platforms:[/dim] [cyan]{', '.join(platforms)}[/cyan]",
        border_style="green",
    ))

    audio_path = video_raw_path = video_final_path = ""
    post_response: dict = {}

    # Step 1 — Audio
    try:
        console.print("\n[bold][1/4][/bold] Generating voiceover via ElevenLabs...")
        audio_path = ElevenLabsClient(
            os.environ["ELEVENLABS_API_KEY"],
            os.environ["ELEVENLABS_VOICE_ID"],
        ).generate_audio(script)
        console.print(f"[green]     \u2713[/green] {audio_path}")
    except Exception as e:
        console.print(f"[bold red]     \u2717 Audio failed:[/bold red] {e}")
        sys.exit(1)

    # Step 2 — Video
    try:
        console.print("\n[bold][2/4][/bold] Generating video via Grok Imagine...")
        video_raw_path = GrokVideoClient(
            os.environ["GROK_API_KEY"],
            os.environ["GROK_BASE_IMAGE_PATH"],
        ).create_video(audio_path, script, setting)
        console.print(f"[green]     \u2713[/green] {video_raw_path}")
    except Exception as e:
        console.print(f"[bold red]     \u2717 Video failed:[/bold red] {e}")
        sys.exit(1)

    # Step 3 — Process
    try:
        console.print("\n[bold][3/4][/bold] Processing video (9:16, trim)...")
        video_final_path = VideoProcessor().process(video_raw_path)
        console.print(f"[green]     \u2713[/green] {video_final_path}")
    except Exception as e:
        console.print(f"[bold red]     \u2717 Processing failed:[/bold red] {e}")
        sys.exit(1)

    # Step 4 — Post
    if skip_post:
        console.print("\n[dim][4/4] Skipping post (--skip-post).[/dim]")
    else:
        try:
            console.print(f"\n[bold][4/4][/bold] Posting to {', '.join(platforms)}...")
            post_response = AyrshareClient(os.environ["AYRSHARE_API_KEY"]).post_video(
                video_final_path, final_caption, hashtag_list, platforms,
            )
            console.print("[green]     \u2713 Posted![/green]")
        except Exception as e:
            console.print(f"[bold red]     \u2717 Posting failed:[/bold red] {e}")
            sys.exit(1)

    # Summary
    t = Table(title="Summary", border_style="green", show_header=False)
    t.add_column(style="dim")
    t.add_column(style="cyan")
    t.add_row("Audio", audio_path)
    t.add_row("Raw Video", video_raw_path)
    t.add_row("Final Video", video_final_path)
    if post_response:
        t.add_row("Post ID", str(post_response.get("id", "see response")))
    console.print(t)

    console.print("\n[bold green]\u2713 Done![/bold green]")


if __name__ == "__main__":
    main()
