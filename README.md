# AI Clone Video System

Fully automated pipeline: script → ElevenLabs voice → Grok Imagine frames → stitched MP4 → Ayrshare → Instagram Reels + TikTok.

## Overview

This system:
1. Accepts a user-provided script and scene setting
2. Generates a realistic voiceover using ElevenLabs Professional Voice Cloning
3. Generates 10 AI image frames via the Grok Imagine API (xAI) with motion-variant prompts
4. Stitches frames into a video at 8 fps with audio overlaid
5. Post-processes the video to 9:16 (1080x1920), trims to 89s max
6. Publishes the video to Instagram Reels and TikTok via Ayrshare

## Prerequisites

- **Python 3.10+**
- **ffmpeg** installed system-wide and available on PATH
- API accounts:
  - [ElevenLabs](https://elevenlabs.io/) — Professional Voice Cloning
  - [xAI / Grok](https://x.ai/) — Image generation
  - [Ayrshare](https://www.ayrshare.com/) — Social media posting

## Installation

```bash
git clone <repo> && cd ai-clone-video
pip install -r requirements.txt
cp .env.template .env   # fill in keys
mkdir assets
# add your photo as assets/base_image.jpg
```

## API Keys Reference

| Service | Where to get it |
|---------|----------------|
| ElevenLabs API key | elevenlabs.io → Profile → API Key |
| ElevenLabs Voice ID | Voice Library → click your cloned voice → ID in URL |
| xAI / Grok key | console.x.ai → API Keys |
| Ayrshare key | app.ayrshare.com → Settings → API Key |

## Usage

```bash
# Full run
python generate_and_post.py \
  --script "Welcome to the future of AI video." \
  --setting "Futuristic laboratory with holographic displays" \
  --caption "My AI clone is here" \
  --hashtags "#AI,#AIClone,#TechTok"

# Video only, no posting
python generate_and_post.py \
  --script "Your script." --setting "Your scene." --skip-post
```

## Output Files

| File | Description |
|------|-------------|
| `output/audio.mp3` | Generated voiceover audio from ElevenLabs |
| `output/frame_*.png` | Temporary Grok-generated image frames (cleaned up after stitching) |
| `output/video_raw.mp4` | Stitched video from image frames + audio |
| `output/video_final.mp4` | Post-processed video (9:16, trimmed, correct codecs) |

## How Grok Video Works

The xAI Grok Imagine API generates images, not video directly. This system:
1. Builds a base prompt from the setting + script excerpt with cinematic quality keywords
2. Generates 10 image frames, each with a different motion modifier (e.g. "subtle zoom in", "slight pan left", "warm golden lighting shift")
3. Stitches frames into a video using moviepy's `ImageSequenceClip` at 8 fps
4. Overlays the ElevenLabs audio track, matching video duration to audio duration
5. Exports at 30 fps with libx264 codec

## Common Errors

| Error | Meaning |
|-------|---------|
| Missing environment variables | Required API keys not set in `.env` |
| ElevenLabs API error (HTTP 401) | Invalid API key or voice ID |
| xAI image generation failed (HTTP 401) | Invalid Grok API key |
| xAI image generation failed (HTTP 429) | Rate limited — wait and retry |
| ffmpeg not found | Install ffmpeg: `brew install ffmpeg` or `apt install ffmpeg` |
| Base image missing | Add your photo to the path in `GROK_BASE_IMAGE_PATH` |
| Ayrshare post failed | Social account not connected or API key invalid |

## Extending

- **Add HeyGen support**: Create `modules/heygen_client.py` with a `create_video(audio_path, script, setting) -> str` method, add provider switching in `generate_and_post.py`
- **Add scheduling**: Use Ayrshare's `scheduleDate` field in the post payload
- **Batch from file**: Read scripts from a `scripts.txt` and loop through `main()` for each line
