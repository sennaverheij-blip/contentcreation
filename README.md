# AI Clone Video System

Fully automated pipeline that generates AI clone videos and publishes them to social media.

## Overview

This system:
1. Accepts a user-provided script and scene setting
2. Generates a realistic voiceover using ElevenLabs Professional Voice Cloning
3. Produces an AI video clone (via HeyGen or Grok/xAI)
4. Post-processes the video to meet platform specs (9:16, correct duration)
5. Publishes the video to Instagram Reels and TikTok (via Ayrshare or Taisly)

## Prerequisites

- **Python 3.10+**
- **ffmpeg** installed and available on PATH
- API accounts for:
  - [ElevenLabs](https://elevenlabs.io/) — Professional Voice Cloning
  - [HeyGen](https://www.heygen.com/) or [xAI](https://x.ai/) — Video generation
  - [Ayrshare](https://www.ayrshare.com/) or [Taisly](https://taisly.com/) — Social media posting

## Installation

```bash
git clone <repo>
cd ai-clone-video
pip install -r requirements.txt
cp .env.template .env
# Edit .env with your API keys
```

## Setup Per Service

### ElevenLabs
- Sign up at [elevenlabs.io](https://elevenlabs.io/)
- Create a Professional Voice Clone from your audio samples
- Copy your API key from Profile > API Key
- Copy the Voice ID from the voice settings page

### HeyGen (Video Provider)
- Sign up at [heygen.com](https://www.heygen.com/)
- Create an avatar or use an existing one
- Copy your API key from Settings > API
- Copy your Avatar ID from the avatar details page

### Grok / xAI (Alternative Video Provider)
- Sign up at [x.ai](https://x.ai/)
- Get your API key from the developer console
- Provide a base image of yourself at the path specified in `.env`

### Ayrshare (Social Posting)
- Sign up at [ayrshare.com](https://www.ayrshare.com/)
- Connect your Instagram and TikTok accounts
- Copy your API key from the dashboard

### Taisly (Alternative Social Posting)
- Sign up at [taisly.com](https://taisly.com/)
- Connect your social accounts
- Copy your API key and User ID from settings

## Usage

```bash
python generate_and_post.py \
  --script "Welcome to the future of AI video." \
  --setting "Futuristic laboratory with holographic displays" \
  --caption "Check out my AI clone!" \
  --hashtags "#AI,#AIClone,#TechContent"
```

Generate only, no posting:

```bash
python generate_and_post.py \
  --script "Welcome to the future of AI video." \
  --setting "Futuristic laboratory with holographic displays" \
  --skip-post
```

## Switching Providers

Edit your `.env` file to change providers:

- **Video provider**: Set `VIDEO_PROVIDER` to `heygen` or `grok`
- **Social provider**: Set `SOCIAL_PROVIDER` to `ayrshare` or `taisly`
- **Target platforms**: Set `TARGET_PLATFORMS` to a comma-separated list (e.g. `instagram,tiktok`)

## Output Files

| File | Description |
|------|-------------|
| `output/audio.mp3` | Generated voiceover audio from ElevenLabs |
| `output/video_raw.mp4` | Raw AI-generated video from HeyGen or Grok |
| `output/video_final.mp4` | Post-processed video (9:16, trimmed, correct codecs) |

## Error Handling

| Error | Meaning |
|-------|---------|
| Missing environment variables | Required API keys not set in `.env` |
| ElevenLabs API error (HTTP 4xx) | Invalid API key, voice ID, or request |
| HeyGen video generation timed out | Video took longer than 10 minutes to generate |
| HeyGen video generation failed | Avatar or audio issue — check HeyGen dashboard |
| Ayrshare/Taisly post failed | Social account not connected or API key invalid |

## Extending the System

To add a new video provider:
1. Create `modules/your_provider_client.py` with a `create_video(audio_path, script, setting) -> str` method
2. Add the provider option to `generate_and_post.py` in the Step B section
3. Add required env vars to `.env.template` and the validation list

To add a new social posting provider:
1. Create `modules/your_social_client.py` with a `post_video(video_path, caption, hashtags, platforms) -> dict` method
2. Add the provider option to `generate_and_post.py` in the Step D section
3. Add required env vars to `.env.template` and the validation list
