# slack-meme-poster (7-claude)

Posts a random meme to Slack every Friday at 16:00 Europe/Brussels.

Webhook-only — no bot token needed. The trick: nginx serves the
`memes/already-sent/` directory at a public URL you control, and the cron job
moves a meme into that directory *before* POSTing the webhook so Slack can
fetch the image.

## How it fits together

```
cron (Fri 16:00)  ─►  pick a random file from memes/
                  ─►  mv  memes/<file>  →  memes/already-sent/<file>
                  ─►  POST { image_url: "$PUBLIC_MEMES_URL/<file>" }
                       to $SLACK_WEBHOOK_URL
                                            │
Slack's image-fetcher  ◄────────────────────┘
                  ─►  GET  $PUBLIC_MEMES_URL/<file>   (hits your nginx)
```

`PUBLIC_MEMES_URL` must point at the nginx service from the **public internet**
— through your reverse proxy / fixed IP / tunnel. Slack's servers fetch it, not
your laptop.

## Setup

```sh
cp .env.example .env       # then edit
docker compose build
docker compose up -d
```

Drop image files (`.jpg .jpeg .png .gif .webp`) into `memes/`. They move to
`memes/already-sent/` as they get posted.

## Verify before Friday

The script accepts `--dry-run` — picks a meme, prints the payload it *would*
have sent, and does **not** move the file or POST anything:

```sh
docker compose run --rm poster python /app/post_meme.py --dry-run
```

To actually fire a post right now (real Slack message, file moves):

```sh
docker compose run --rm poster python /app/post_meme.py
```

Check that nginx is serving (locally, then through the public URL):

```sh
curl -I http://localhost:4001/cat.jpg                       # after the file has been moved
curl    http://localhost:4001/healthz                       # always returns "ok"
curl -I http://itenium-test.synology.me:4001/healthz        # confirms router forward + DDNS
```

## Tests

```sh
cd poster
python -m venv .venv && .venv/bin/pip install -r requirements.txt pytest
.venv/bin/pytest
```

## Files

| Path                    | What                                                                |
|-------------------------|---------------------------------------------------------------------|
| `poster/post_meme.py`   | Pick → move → POST. `--dry-run` for safe verification.              |
| `poster/Dockerfile`     | python:3.12-alpine + tini + crond.                                  |
| `poster/entrypoint.sh`  | Propagates env into cron's child shell; sets TZ.                    |
| `nginx/nginx.conf`      | Serves only `already-sent/`, no autoindex, 30d cache headers.       |
| `docker-compose.yml`    | poster + nginx, shared `./memes` volume.                            |
| `.env.example`          | Template; copy to `.env`.                                           |

## Why webhook + nginx instead of a bot token

A bot token + `files_upload_v2` is the cleaner Slack-side approach (no public
hosting needed). This stack uses a webhook because you already had one from a
previous attempt, and a publicly-reachable docker host. Tradeoffs:

- **You expose an HTTP surface.** Mitigated by `autoindex off` and only serving
  `already-sent/`.
- **Slack fetches `image_url` server-side.** If the box is down at fetch time,
  the message posts with no image and stays broken — re-posting is the fix.
- **Webhook URL doesn't expire** the way bot tokens can; once you have it, it
  keeps working until you rotate it.
