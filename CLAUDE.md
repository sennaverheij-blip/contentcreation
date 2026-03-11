# AI Clone Video System — Instructions

## Overview
Fully automated pipeline that accepts a script + scene setting, generates a realistic voiceover (ElevenLabs), produces an AI video via Grok Imagine (xAI), post-processes the video for social platforms, and publishes to Instagram Reels and TikTok via Ayrshare.

## Architecture
All logic lives in `generate_and_post.py`. All secrets live in `.env`. Never hardcode API keys.

## Key Files
- `generate_and_post.py` — CLI orchestrator (click + rich)
- `modules/elevenlabs_client.py` — ElevenLabs TTS voice cloning
- `modules/grok_video_client.py` — xAI Grok image generation + frame stitching
- `modules/video_processor.py` — moviepy post-processing (9:16, trim, codecs)
- `modules/ayrshare_client.py` — Ayrshare social media posting

## Constraints
- All API keys from `os.environ` via `python-dotenv`
- Every API call must have error handling with descriptive `RuntimeError`
- Video output: 1080x1920, libx264, aac, 30fps, max 89s
- `output/` directory created automatically if missing
