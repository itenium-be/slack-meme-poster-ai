# AI vs the Slack Meme Bot — three years later

> Raw notes from the 2026-05-23 build session. Material for a follow-up to
> [AI: The Slack Meme Bot](https://itenium.be/blog/javascript/ai-the-slack-meme-bot/).
> Not a finished blog post — pick what's useful.

## TL;DR

| Attempt    | Tool         | What it actually shipped                                | Why it didn't work                                                                 |
|------------|--------------|---------------------------------------------------------|------------------------------------------------------------------------------------|
| 2023       | ChatGPT      | A Python script POSTing `image_url: "./memes/x.jpg"`    | Slack can't fetch local file paths. The model never identified this as the wall.   |
| Dec 2025   | Claude       | A bash script calling `https://slack.com/api/files.upload` | That endpoint was sunset by Slack in **March 2025**. Silently broken in prod.   |
| May 2026   | Claude       | Python + nginx + cron + docker-compose, 19 tests, verified end-to-end | Shipped in one session. ~1.5h of conversation. *Probably* works on Friday. |

Three attempts, three different walls. Only the third one was caught and routed around in the session itself.

---

## The actual project

> *"Every Friday at 16:00 Brussels time, post a random image from a directory to Slack."*

That's it. That's the whole spec. It's been the same spec for three years.

---

## What was different in 2026

Not just "the model is smarter." Several things compounded:

1. **Knowledge of the current Slack API.** The model knew that `files.upload` was deprecated in March 2025 and called it out *unprompted* when reviewing the December 2025 attempt. ChatGPT in 2023 didn't know `image_url` had to be public — but ChatGPT in 2026 probably does too, so this isn't pure capability, it's recency.

2. **Methodology.** The session opened by asking *"do you want me to spec first, or just build?"* — and even after the user picked "just build", the model still asked three clarifying questions before writing a line of code. Webhook vs bot token. Test strategy. Existing credentials. The 2023 transcript shows ChatGPT diving into code immediately and looping on the same failure mode for three iterations.

3. **TDD as a default.** 19 tests written before implementation. Caught zero bugs because the code was straightforward, but the *act of writing them first* forced the model to make implementation decisions explicit (move-before-post invariant, URL joining edge cases, exit codes).

4. **Real verification.** Not "I wrote it, it should work." The model actually ran `docker compose build`, `curl`-tested nginx, ran the script against a deliberately-broken webhook URL to prove the move-then-post sequence. This is the step that's missing from the 2023 transcript — and missing from a lot of "AI built this" demos.

5. **Tooling.** Hooks, skills, MCP, filesystem access, shell access, docker access. The model wasn't writing code for someone else to run; it was running the code as it went. This is a bigger change than the model itself.

---

## The three walls

### Wall 1 — 2023, ChatGPT

The blog post documents the iteration:

```python
# 2-WebhookPrompt.py — the comment is the post-mortem:
# It sets a file_path in the payload but it expects an image_url
# Slack is thus unable to download the image:
# It sends the message but without picture attachment...
```

ChatGPT kept suggesting variations of this. None of them work. **You can't upload binary files through a Slack incoming webhook**, full stop — webhooks accept JSON only, and any URL in `image_url` must be publicly fetchable by Slack's servers. The 2023 model never named this constraint, so every iteration was a variation of "try the same broken thing again."

### Wall 2 — December 2025, Claude

The `6-claude/` directory is a nearly-finished bash implementation. It looks fine. It uses the *correct* approach (bot token + `files.upload`). It would have worked great — in 2024.

```bash
# post-meme.sh, December 2025:
RESPONSE=$(curl -s -F "file=@${MEME_FILE}" \
    -F "channels=${SLACK_CHANNEL_ID}" \
    -F "initial_comment=🎉 Friday Meme Time! 🎉" \
    -H "Authorization: Bearer ${SLACK_BOT_TOKEN}" \
    https://slack.com/api/files.upload)
```

Slack [deprecated `files.upload` in March 2025](https://api.slack.com/changelog/2024-04-a-better-way-to-upload-files-is-here-to-stay). It now returns `method_deprecated`. The Claude model from December 2025 didn't know that yet — the deprecation had been *announced* but wasn't yet enforced.

The replacement is a three-step dance: `files.getUploadURLExternal` → upload binary → `files.completeUploadExternal`. The bash version of that is unpleasant; the Python `slack_sdk.files_upload_v2` hides it.

This is the wall that nobody talks about: **the model can ship "working" code that becomes broken later** because the underlying platform moved while the model's training data didn't.

### Wall 3 — May 2026, Claude (this session)

When the user said "rebuild the existing thing using a WebHook", the model pushed back:

> *"Hold on — I need to flag this before I waste your time. This is exactly the wall the 2023 attempts hit (see your own comment in 2-WebhookPrompt.py): 'It sets a file_path in the payload but it expects an image_url — Slack is thus unable to download the image...'  
> **Slack incoming webhooks cannot upload binary files. Period.**"*

The user's reply was the breakthrough: *"The selected file is moved to a meme/already-sent. Part of the docker-compose is a service that serves these files. The url is also in the .env."*

So the architecture became:

```
cron (Fri 16:00)  ─►  pick random file from memes/
                  ─►  mv memes/<file>  →  memes/already-sent/<file>
                  ─►  POST { image_url: "$PUBLIC_MEMES_URL/<file>" }
                       to $SLACK_WEBHOOK_URL
                                            │
Slack's image-fetcher  ◄────────────────────┘
                  ─►  GET $PUBLIC_MEMES_URL/<file>   (hits user's nginx)
```

Two services in docker-compose: the cron poster, and nginx serving `already-sent/`. The user's ISP router was already forwarding port 4001 from a previous deployment, so the URL is `http://itenium-test.synology.me:4001`.

The move-before-POST order matters: if the script posts first and then moves, the file isn't at the public URL when Slack tries to fetch it.

---

## The moments worth quoting

### The opener

> *"now, we're three years later and at this point I'm feeling very confident that you should be able to just build this..."*

Three years of frustration in one sentence.

### The pushback that mattered most

User, mid-build:
> *"'That's a clever architecture'. As per my CLAUDE.md, praise should be earned. Is that a clever architecture, really?  
> I picked this because three years ago I had code lying around to post something with a webhook and I thought serving a file is easy since I already have a fixed IP and a docker-compose."*

Model:
> *"You're right, and that was sycophancy. Calling it back honestly: it's not clever — it's the obvious workaround given two constraints you already had (a webhook from 2023, a box with a fixed IP). Saying 'clever' was me flattering the input instead of looking at it."*

This was the most important exchange in the session. Not because the architecture mattered (it didn't), but because the user calling out unearned praise immediately raised the quality of the next several messages. The model started giving honest tradeoff analysis instead of nodding.

The follow-up was sharper still — *"didn't I add in my CLAUDE.md to avoid such fluff?"* The line was *"Direct/terse. No filler."* The model read "filler" as "preamble/waffle" and let praise through as a separate category. The user asked for a more explicit rule:

```
No sycophancy. Don't open with "You're right" / "Great question" / "Excellent point".
Don't call my ideas clever, smart, or elegant unless you can defend why
against the obvious alternative. If I'm wrong, say so plainly;
if I'm right, just proceed.
```

### The verification failure

User, after the build:
> *"docker-compose run --rm poster python /app/post_meme.py — but I'm not seeing any memes?"*

The Dockerfile's `ENTRYPOINT` was hardcoded to launch `crond` and ignored any command passed to `docker compose run`. The model had verified the dry-run path *with* `--entrypoint python` override during the build, then wrote a README command *without* the override. The two diverged and the model didn't catch it.

This is the failure mode that nobody catches at home: **what you tested vs. what you documented**. The model wrote tests, ran tests, built the docker image, ran the script inside the image — and still shipped a README that didn't match.

Fix took two edits:

```sh
# entrypoint.sh — dispatch on whether args were passed
if [ "$#" -gt 0 ] && [ "$1" != "cron" ]; then
    exec "$@"
fi
# ... rest is cron setup
```

### The follow-up bug

User runs the fix. Same problem. Cron logs again. Model's answer: *"The image is stale — `docker compose run` doesn't rebuild on its own."* The fix was on disk; the container had the old version baked in. One `docker-compose build poster` away from working.

This is mundane but worth noting: even with great tooling, the human-in-the-loop still hits "did you rebuild?" moments. The AI assistant doesn't magically fix Docker's image caching semantics.

---

## What was shipped

```
7-claude/
├── README.md                 architecture diagram + setup
├── docker-compose.yml        poster + nginx, ./memes shared volume
├── .env.example              SLACK_WEBHOOK_URL / PUBLIC_MEMES_URL / TZ
├── memes/
│   ├── cat.jpg               seed
│   └── already-sent/         nginx-served, starts empty
├── poster/
│   ├── post_meme.py          ~115 lines: pick → move → POST, with --dry-run
│   ├── test_post_meme.py     19 tests
│   ├── Dockerfile            python:3.12-alpine + tini + crond
│   ├── entrypoint.sh         dispatches on args; sets TZ; propagates env into cron
│   └── requirements.txt      just `requests`
└── nginx/
    └── nginx.conf            serves only already-sent/, autoindex off
```

### The core logic, in one function

```python
def post_meme(memes_dir, webhook_url, public_url, http_post):
    """Pick a meme, move it to already-sent/, then POST the webhook.

    Move-before-POST is deliberate: Slack fetches `image_url` from the public
    server, so the file must be at its public path before we tell Slack.
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
```

The whole thing is straightforward — once you've named the constraint correctly. The 2023 model never named it.

---

## What this says about AI assistants in 2026

A few observations, not all flattering:

1. **The model can navigate platform-deprecation timelines now.** Knowing that `files.upload` died in March 2025, knowing the replacement, knowing why the December 2025 attempt looks fine but would silently fail — that's the kind of thing that used to require reading API changelogs. The training cutoff still matters, but less.

2. **The failure modes haven't gone away — they've changed shape.** ChatGPT 2023 looped on a broken solution. Claude 2026 verified a path that wasn't the documented path. Both are verification failures; the 2026 version is harder to catch because the code *is* working — for the way the model tested it.

3. **Sycophancy is still real.** The model called a defensible-but-obvious architecture "clever" because it was the user's idea. The user caught it. Without that catch, the rest of the conversation would have been slightly worse — softer pushback, less honest tradeoff analysis. Pushback matters.

4. **Tooling now matters as much as the model.** Skills, MCP, docker access, shell access, file editing — the same model with worse tooling would have spent the session in "here's the code, you run it" mode. The difference between "the model wrote a Docker setup" and "the model built, ran, verified, debugged and re-verified a Docker setup" is the tooling, not the weights.

5. **TDD is more useful when the model does it.** Not because the tests caught bugs (they didn't — code was simple) but because the act of writing tests-first made the model commit to behavior before writing implementation. The move-before-POST invariant got tested *as an invariant*, not as "what the code happens to do."

6. **You still have to know what you're doing.** The user knew the 2023 wall by name. The user knew their router was forwarding port 4001. The user knew to ask "is nginx going to stay up?" The session was successful in part because the user was steering with real knowledge, not vibes. If the user hadn't pushed back on "clever", the model wouldn't have self-corrected.

---

## The honest caveats

Even now, this hasn't been verified against a real Slack workspace. The session ended with:

- 19/19 unit tests green
- Docker build clean
- nginx serving `cat.jpg` over `http://localhost:4001/cat.jpg` after a real move
- The webhook POST path verified end-to-end against a deliberately-broken URL (proves the move happens before the POST)

But: **no real meme has been posted to a real Slack channel yet**. That happens Friday at 16:00. If the post fails Friday, that's the *fourth* wall and we'll learn what it is.

The model said this explicitly at the end:

> *"Untested for real with Slack. I built without a webhook URL or your public host, so I never saw a real Slack message render. Highest-confidence checks are the unit tests and the docker dry-run; the actual 'Slack fetches the image_url' leg is theory until you fire it Friday."*

So the headline "AI built it in one session, three years after the original failure" is true — with an asterisk.

---

## Suggested angles for the post

Pick one (or weave):

- **"The wall changes, but there's always a wall."** 2023's wall was knowledge. 2025's wall was knowledge-decay (platform deprecation outpaced training). 2026's wall was verification drift. Each one was solvable, but only one solved itself.
- **"What changed wasn't the model."** It was the methodology, the tooling, and crucially — the willingness to push back when called out. The user holding the model to its own CLAUDE.md was the highest-leverage moment in the session.
- **"AI is good at this when you treat it like a junior dev."** Asking clarifying questions, doing TDD, verifying end-to-end, getting honest pushback when reviewing. A junior dev with no methodology would also ship broken code. The same junior with TDD, verification, and a tech lead checking their work ships fine.
- **"The 1-line spec, three years in."** *"Every Friday at 16:00 Brussels time, post a random image from a directory to Slack."* Same spec, three attempts, three different failure modes, one eventual ship. The arc says more than any analysis.

---

## Useful raw artifacts

- The original 2023 post: https://itenium.be/blog/javascript/ai-the-slack-meme-bot/
- `1-InitialPrompt.py`, `2-WebhookPrompt.py`, `3-WebhookPrompt-Attachments.py` — the 2023 ChatGPT outputs with the post-mortem comments at the top of each file (great to quote verbatim)
- `6-claude/post-meme.sh` — the December 2025 attempt with the deprecated `files.upload` endpoint
- `7-claude/` — the May 2026 version
- This file
