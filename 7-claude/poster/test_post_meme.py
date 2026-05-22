from __future__ import annotations

import random
from pathlib import Path
from typing import Any

import pytest

from post_meme import build_payload, main, pick_random_meme, post_meme


class FakeWebhook:
    """Records calls so tests can assert on URL + JSON without real HTTP."""

    def __init__(self, status: int = 200) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.status = status

    def __call__(self, url: str, json: dict[str, Any]) -> int:
        self.calls.append((url, json))
        return self.status


@pytest.fixture
def memes_dir(tmp_path: Path) -> Path:
    (tmp_path / "already-sent").mkdir()
    return tmp_path


def test_pick_random_meme_returns_a_file_from_the_directory(memes_dir: Path) -> None:
    (memes_dir / "cat.jpg").write_bytes(b"\x89PNG")
    assert pick_random_meme(memes_dir) == memes_dir / "cat.jpg"


def test_pick_random_meme_returns_none_when_directory_has_no_memes(memes_dir: Path) -> None:
    assert pick_random_meme(memes_dir) is None


def test_pick_random_meme_ignores_already_sent_subdirectory(memes_dir: Path) -> None:
    (memes_dir / "already-sent" / "old.jpg").write_bytes(b"x")
    assert pick_random_meme(memes_dir) is None


def test_pick_random_meme_accepts_common_image_extensions(memes_dir: Path) -> None:
    for name in ["a.jpg", "b.jpeg", "c.png", "d.gif", "e.webp"]:
        (memes_dir / name).write_bytes(b"x")
    chosen = pick_random_meme(memes_dir)
    assert chosen is not None
    assert chosen.suffix.lower() in {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def test_pick_random_meme_skips_non_image_files(memes_dir: Path) -> None:
    (memes_dir / "notes.txt").write_bytes(b"hi")
    (memes_dir / "README.md").write_bytes(b"hi")
    assert pick_random_meme(memes_dir) is None


def test_pick_random_meme_is_actually_random(memes_dir: Path) -> None:
    # Seed picks differently — proves we're using random choice, not "first file".
    for name in ["a.jpg", "b.jpg", "c.jpg", "d.jpg", "e.jpg"]:
        (memes_dir / name).write_bytes(b"x")

    random.seed(1)
    first = pick_random_meme(memes_dir)
    random.seed(2)
    second = pick_random_meme(memes_dir)
    assert first != second


# ---------------- build_payload ----------------


def test_build_payload_image_url_joins_public_base_and_filename() -> None:
    payload = build_payload(filename="cat.jpg", public_url="https://m.example.com")
    image_block = next(b for b in payload["blocks"] if b["type"] == "image")
    assert image_block["image_url"] == "https://m.example.com/cat.jpg"


def test_build_payload_strips_trailing_slash_on_public_url() -> None:
    payload = build_payload(filename="cat.jpg", public_url="https://m.example.com/")
    image_block = next(b for b in payload["blocks"] if b["type"] == "image")
    assert image_block["image_url"] == "https://m.example.com/cat.jpg"


def test_build_payload_includes_fallback_text_for_notifications() -> None:
    # Without top-level text, Slack push notifications and link previews are empty.
    payload = build_payload(filename="cat.jpg", public_url="https://m.example.com")
    assert payload.get("text")


def test_build_payload_alt_text_is_filename_for_accessibility() -> None:
    payload = build_payload(filename="cat.jpg", public_url="https://m.example.com")
    image_block = next(b for b in payload["blocks"] if b["type"] == "image")
    assert image_block["alt_text"] == "cat.jpg"


# ---------------- post_meme orchestrator ----------------


def test_post_meme_moves_file_to_already_sent_before_posting(memes_dir: Path) -> None:
    cat = memes_dir / "cat.jpg"
    cat.write_bytes(b"x")
    webhook = FakeWebhook()

    # Snapshot whether the file existed in already-sent at the moment the webhook
    # was called — proves the move happens *before* the POST, not after.
    moved_at_post_time: list[bool] = []

    def assert_moved(url: str, json: dict[str, Any]) -> int:
        moved_at_post_time.append((memes_dir / "already-sent" / "cat.jpg").exists())
        return webhook(url, json)

    result = post_meme(
        memes_dir=memes_dir,
        webhook_url="https://hooks.slack.test/x",
        public_url="https://m.example.com",
        http_post=assert_moved,
    )

    assert result == memes_dir / "already-sent" / "cat.jpg"
    assert not cat.exists()
    assert (memes_dir / "already-sent" / "cat.jpg").exists()
    assert moved_at_post_time == [True]


def test_post_meme_posts_to_webhook_url_with_image_url_for_chosen_file(
    memes_dir: Path,
) -> None:
    (memes_dir / "only.png").write_bytes(b"x")
    webhook = FakeWebhook()

    post_meme(
        memes_dir=memes_dir,
        webhook_url="https://hooks.slack.test/x",
        public_url="https://m.example.com",
        http_post=webhook,
    )

    assert len(webhook.calls) == 1
    url, payload = webhook.calls[0]
    assert url == "https://hooks.slack.test/x"
    image_block = next(b for b in payload["blocks"] if b["type"] == "image")
    assert image_block["image_url"] == "https://m.example.com/only.png"


def test_post_meme_returns_none_and_does_not_post_when_no_memes(memes_dir: Path) -> None:
    webhook = FakeWebhook()

    result = post_meme(
        memes_dir=memes_dir,
        webhook_url="https://hooks.slack.test/x",
        public_url="https://m.example.com",
        http_post=webhook,
    )

    assert result is None
    assert webhook.calls == []


def test_post_meme_raises_when_webhook_returns_non_2xx(memes_dir: Path) -> None:
    (memes_dir / "cat.jpg").write_bytes(b"x")
    webhook = FakeWebhook(status=500)

    with pytest.raises(RuntimeError, match="500"):
        post_meme(
            memes_dir=memes_dir,
            webhook_url="https://hooks.slack.test/x",
            public_url="https://m.example.com",
            http_post=webhook,
        )


# ---------------- main CLI ----------------


def _env(memes_dir: Path, **overrides: str) -> dict[str, str]:
    base = {
        "SLACK_WEBHOOK_URL": "https://hooks.slack.test/x",
        "PUBLIC_MEMES_URL": "https://m.example.com",
        "MEMES_DIR": str(memes_dir),
    }
    base.update(overrides)
    return base


def test_main_exits_nonzero_when_webhook_url_missing(
    memes_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for k, v in _env(memes_dir).items():
        monkeypatch.setenv(k, v)
    monkeypatch.delenv("SLACK_WEBHOOK_URL")
    assert main([]) != 0


def test_main_exits_nonzero_when_public_url_missing(
    memes_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for k, v in _env(memes_dir).items():
        monkeypatch.setenv(k, v)
    monkeypatch.delenv("PUBLIC_MEMES_URL")
    assert main([]) != 0


def test_main_dry_run_does_not_move_file_or_call_webhook(
    memes_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cat = memes_dir / "cat.jpg"
    cat.write_bytes(b"x")
    for k, v in _env(memes_dir).items():
        monkeypatch.setenv(k, v)

    webhook = FakeWebhook()
    monkeypatch.setattr("post_meme._http_post", webhook)

    exit_code = main(["--dry-run"])

    assert exit_code == 0
    assert cat.exists()  # not moved
    assert not (memes_dir / "already-sent" / "cat.jpg").exists()
    assert webhook.calls == []  # no HTTP


def test_main_returns_zero_when_no_memes_to_post(
    memes_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for k, v in _env(memes_dir).items():
        monkeypatch.setenv(k, v)
    monkeypatch.setattr("post_meme._http_post", FakeWebhook())
    assert main([]) == 0


def test_main_posts_when_a_meme_exists(
    memes_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (memes_dir / "cat.jpg").write_bytes(b"x")
    for k, v in _env(memes_dir).items():
        monkeypatch.setenv(k, v)
    webhook = FakeWebhook()
    monkeypatch.setattr("post_meme._http_post", webhook)

    assert main([]) == 0
    assert len(webhook.calls) == 1
