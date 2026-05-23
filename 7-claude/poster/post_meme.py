from __future__ import annotations

import argparse
import json
import os
import random
import sys
from pathlib import Path
from typing import Any, Callable, Optional, Sequence

# Slack's image unfurl supports these; gif/webp render as static previews.
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

# Type of the injected HTTP poster: (url, json) -> status_code.
HttpPost = Callable[[str, dict[str, Any]], int]


def pick_random_meme(memes_dir: Path) -> Path | None:
    """Return a random image file from memes_dir, ignoring its already-sent/ subdir.

    Returns None when no eligible files exist — caller decides whether that's an
    error or just a quiet Friday.
    """
    candidates = [
        p
        for p in memes_dir.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    ]
    if not candidates:
        return None
    return random.choice(candidates)


def build_payload(filename: str, public_url: str) -> dict[str, Any]:
    """Build the webhook JSON. Uses Block Kit so the image renders inline.

    `text` is a notification fallback — without it, push/desktop notifications
    show an empty body.
    """
    image_url = f"{public_url.rstrip('/')}/{filename}"
    return {
        "text": f"🎉 Friday Meme Time! ({filename})",
        "blocks": [
            {
                "type": "image",
                "image_url": image_url,
                "alt_text": filename,
            }
        ],
    }


def post_meme(
    memes_dir: Path,
    webhook_url: str,
    public_url: str,
    http_post: HttpPost,
) -> Optional[Path]:
    """Pick a meme, move it to already-sent/, then POST the webhook.

    Move-before-POST is deliberate: Slack fetches `image_url` from the public
    server, so the file must be at its public path before we tell Slack about it.

    Returns the new path of the posted file, or None if no memes were available.
    Raises RuntimeError on a non-2xx webhook response; the file stays moved
    (the meme is "spent" — re-running picks a different one).
    """
    chosen = pick_random_meme(memes_dir)
    if chosen is None:
        return None

    sent_dir = memes_dir / "already-sent"
    sent_dir.mkdir(exist_ok=True)
    destination = sent_dir / chosen.name
    chosen.rename(destination)

    payload = build_payload(filename=destination.name, public_url=public_url)
    status = http_post(webhook_url, payload)
    if not 200 <= status < 300:
        raise RuntimeError(f"Slack webhook returned status {status}")
    return destination


def _http_post(url: str, payload: dict[str, Any]) -> int:
    """Default HTTP poster. Module-level so tests can monkeypatch it."""
    import requests  # imported lazily so tests don't need the dep at import time

    try:
        return requests.post(url, json=payload, timeout=10).status_code
    except requests.exceptions.RequestException as e:
        # Translate to a clean message instead of dumping a full traceback in
        # cron.log when the webhook host is unreachable / DNS fails / times out.
        raise RuntimeError(f"webhook unreachable: {e.__class__.__name__}") from e


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Post a random meme to Slack.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Pick a meme and print the payload, but don't move or POST.",
    )
    args = parser.parse_args(argv)

    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    public_url = os.environ.get("PUBLIC_MEMES_URL")
    memes_dir = Path(os.environ.get("MEMES_DIR", "/memes"))

    missing = [
        name
        for name, value in [
            ("SLACK_WEBHOOK_URL", webhook_url),
            ("PUBLIC_MEMES_URL", public_url),
        ]
        if not value
    ]
    if missing:
        print(f"ERROR: missing required env vars: {', '.join(missing)}", file=sys.stderr)
        return 2

    assert webhook_url is not None and public_url is not None  # for type-checkers

    if args.dry_run:
        chosen = pick_random_meme(memes_dir)
        if chosen is None:
            print(f"No memes found in {memes_dir} (dry-run).")
            return 0
        payload = build_payload(filename=chosen.name, public_url=public_url)
        print(f"DRY-RUN — would POST to {webhook_url}")
        print(json.dumps(payload, indent=2))
        return 0

    try:
        result = post_meme(
            memes_dir=memes_dir,
            webhook_url=webhook_url,
            public_url=public_url,
            http_post=_http_post,
        )
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    if result is None:
        print(f"No memes found in {memes_dir}.")
    else:
        print(f"Posted {result.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
