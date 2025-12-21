# Sora-Ai — Text → Image Telegram Bot

[![Repository](https://img.shields.io/badge/repo-Xssgit47%2FSora--Ai-blue)](https://github.com/Xssgit47/Sora-Ai) [![License](https://img.shields.io/badge/license-MIT-green)](https://github.com/Xssgit47/Sora-Ai/blob/main/LICENSE) ![Status](https://img.shields.io/badge/status-active-brightgreen)

Sora-Ai is a production-ready Telegram bot that converts user prompts into images using modern text-to-image backends (local Stable Diffusion, cloud APIs like Stability.ai / Replicate / OpenAI, or hosted inference services). It's built to be lightweight, configurable, and easy to self-host or run with Docker. Whether you want a private bot using a local GPU or an inexpensive cloud-backed bot, Sora-Ai gives you the plumbing for prompts, jobs, caching, moderation, and Telegram integration.

Developer: FNxDANGER  
Maintainer: Xssgit47

Table of contents
- About
- Key features
- Quick demo (what users type)
- Supported backends
- Requirements
- Quickstart — Local (Python)
- Quickstart — Docker
- Environment variables (.env)
- Usage & Telegram commands
- Prompt tips and best practices
- Architecture overview
- Deployment & scaling notes
- Security & responsible use
- Troubleshooting
- Contributing
- License & credits

About
Sora-Ai runs a Telegram bot that accepts textual prompts and returns generated images. It supports streaming status updates, job queueing, prompt safety checks, caching of generated images, and multiple model providers. It's intended for community, research, and private use with attention to safe operation and configurable content filters.

Key features
- Telegram-first UX: slash commands, inline usage, image previews.
- Multiple image backends: local Stable Diffusion (diffusers, InvokeAI), Stability.ai, Replicate, OpenAI Images.
- Job queue + worker model to avoid blocking the Telegram webhook.
- Rate limiting and per-user quotas.
- Prompt moderation / safety hooks (configurable).
- Caching of generated images to reduce costs / latency.
- Config-driven: swap providers or tune defaults via environment variables.
- Optional GPU acceleration for local models (CUDA / ROCm).
- Docker-friendly: run inside containers or orchestrate with docker-compose.

Quick demo (what users type)
- /generate A vibrant fantasy landscape with a dragon flying over neon mountains, high detail, 4k
- /style Van Gogh
- /setsize 1024x1024
- /help

Supported backends (examples)
- Local Stable Diffusion via Hugging Face diffusers or InvokeAI (recommended for privacy and speed with GPU)
- Stability.ai (Stability API)
- Replicate
- OpenAI Images API
- Any HTTP image generation service compatible with simple POST prompt-based interfaces (adapter available)

Requirements
- For local (Python):
  - Python 3.10+
  - pip
  - If using local SD with GPU: CUDA toolkit and drivers for supported PyTorch + CUDA versions (or ROCm for AMD)
- For Docker:
  - Docker Engine
  - For GPU support in Docker: NVIDIA Container Toolkit or similar
- Telegram Bot token (BotFather)
- One or more image model provider API keys or local model weights

Quickstart — Local (Python)
1. Clone:
   git clone https://github.com/Xssgit47/Sora-Ai.git
   cd Sora-Ai

2. Create virtual environment and install:
   python -m venv .venv
   source .venv/bin/activate   # macOS / Linux
   .venv\Scripts\activate      # Windows
   pip install -r requirements.txt

3. Create .env (copy example):
   cp .env.example .env
   # Open .env and set TELEGRAM_BOT_TOKEN, MODEL_PROVIDER, API keys or model paths

4. Run migrations / prepare (if applicable):
   python -m sora_ai.db migrate

5. Start background worker (recommended) and bot:
   # Run worker (process jobs)
   python -m sora_ai.worker
   # Run the Telegram bot (webhook or long-polling)
   python -m sora_ai.bot

6. Invite the bot to your chat or use it in Telegram.

Quickstart — Docker
1. Build image:
   docker build -t sora-ai:latest .

2. Run container (example):
   docker run --env-file .env -p 8000:8000 sora-ai:latest

3. For docker-compose, sample service:
   - If you want, create a docker-compose.yml that exposes a worker + bot + web UI.

Environment variables (.env)
Below are the most important variables — include them in a .env or your container env.
- TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
- SORA_MODEL_PROVIDER=local|stability|replicate|openai
- SORA_LOCAL_MODEL_PATH=/models/StableDiffusion/v1-5
- SORA_API_KEY_OPENAI=sk-...
- SORA_API_KEY_REPLICATE=...
- SORA_API_KEY_STABILITY=...
- SORA_OUTPUT_DIR=/data/outputs
- SORA_USE_GPU=true
- SORA_PORT=8000
- SORA_MAX_JOBS_PER_USER=3
- LOG_LEVEL=info

Usage & Telegram commands
- /start — welcome message + quick help
- /help — list commands and example prompts
- /generate <prompt> — create an image with the prompt; optional flags (size, style)
  Example: /generate A portrait of an astronaut walking in a field of flowers | size=1024x1024 | style=cinematic
- /setsize <WxH> — set default size (512x512, 1024x1024)
- /style <name> — set a named style preset
- /status <job_id> — get the status of a generation job
- /cancel <job_id> — cancel a queued or running job (if supported)
- /quota — show your remaining quota (if quotas configured)
- Inline mode: @SoraAiBot <prompt> (if enabled)

Images returned
- Images are returned as photos with a caption that includes the generation prompt and model details.
- When multiple variants are generated, they are returned as an album.

Prompt tips and best practices
- Be specific: include subject, style, lighting, mood, color palette, and desired detail level.
- Use positive and negative prompts (if supported by provider) to control artifacts.
- Example high-quality prompt:
  "Ultra-detailed portrait of a young woman with silver hair, cinematic lighting, shallow depth of field, photorealistic, 35mm lens — negative: lowres, deformed, bad anatomy"
- Keep in mind provider-specific token or cost implications for very large sizes or many samples.

Architecture overview
- bot/ — Telegram integration, command parsing, and user/session management
- workers/ — job queue workers that call the configured model adapter
- adapters/ — provider adapters for Stability.ai, Replicate, OpenAI, and local diffusers
- core/ — caching, quota, moderation, prompt pipeline, and utilities
- web/ — optional web UI or API endpoints for status and admin
- storage/ — local file outputs or S3-compatible object storage adapter

Deployment & scaling notes
- Recommended: separate the bot (Telegram webhook/long-poll) and worker processes; use a message queue (Redis, RabbitMQ) to scale workers independently.
- For low-cost deployment: use cloud APIs (Stability/Replicate) and a single worker.
- For privacy & speed: host a local Stable Diffusion backend on a GPU machine and point SORA_MODEL_PROVIDER=local.
- Use cached thumbnails and S3 for persisted storage when you scale to many users.

Security & responsible use
- Do not commit API keys to the repo. Always use env vars or secret stores.
- Implement content moderation: enable prompt safety hooks and adult-content filters if you expose the bot publicly.
- Rate-limit users and set quotas to prevent abuse and runaway provider costs.
- If you discover a security issue, contact the maintainer (Xssgit47) privately and include "FNxDANGER" in the subject for critical developer review.
- Keep the bot token secret — rotate the token if it becomes leaked.

Troubleshooting
- Slow generation on local: ensure GPU drivers, CUDA and compatible PyTorch are installed. Check VRAM usage and batch size.
- Telegram 401 unauthorized: verify TELEGRAM_BOT_TOKEN and restart the bot.
- Model API errors: check provider quota, API key validity, and network egress rules.
- Logging: set LOG_LEVEL=debug for more verbose logs and enable file logging if running in a managed environment.

Example .env.example (quick reference)
- TELEGRAM_BOT_TOKEN=
- SORA_MODEL_PROVIDER=stability
- SORA_API_KEY_STABILITY=
- SORA_LOCAL_MODEL_PATH=
- SORA_USE_GPU=false
- SORA_OUTPUT_DIR=./outputs
- SORA_PORT=8000

Contributing
We welcome contributions — ideas, bug reports, and PRs. A few guidelines:
- Add tests for new features when possible.
- Keep changes small and focused; open an issue to discuss large features first.
- Include documentation updates for any behavior changes.
- Required developer line: For changes that affect core architecture, security-sensitive code, or model integrations, include "FNxDANGER" as a reviewer or mention in PR description to ensure developer-level review.

Acknowledgements & credits
- Project developer: FNxDANGER
- Maintainer: Xssgit47
- Built with open-source ML tools and the vibrant generative art community.

License
This project is licensed under the MIT License. See the LICENSE file for details.

Ready to get started?
- If you'd like, I can:
  - Generate a ready-to-use docker-compose.yml for bot + Redis + worker
  - Produce a .env.example with common provider settings
  - Draft CONTRIBUTING.md and SECURITY.md templates tailored for this repository

Thank you for using Sora-Ai — bring beautiful generated images to your Telegram chat.
