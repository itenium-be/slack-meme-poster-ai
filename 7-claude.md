Claude Code
===========

Three years later; Claude Code should just generate this for me, right?

Initial prompt:

```txt
check current repo. I tried to build the slack-meme-poster back in 2023. AI failed doing
so. I was really disappointed. Also see this blog post I generated after:
https://itenium.be/blog/javascript/ai-the-slack-meme-bot/

now, we're three years later and at this point I'm feeling very confident that you
should be able to just build this...

with the 6-claude folder, it looks like I already tried this back in december 2025.
anyhow.

I want to create this simple app in one go. I see two path:

1) you just go ahead and build it right now in 7-claude

2) you feel like you won't be able to build a working copy of this in one go and you
first create a spec/plan before writing it

which one do you want to do?
```

Questions are asked
-------------------

### Language

```txt
Which implementation language for 7-claude?

  1. Bash + curl (like 6-claude)
     Smallest image, fewest deps. Slightly more awkward for the 3-step Slack v2 upload flow
     but very doable with curl + jq.
  2. Python + slack_sdk
     slack_sdk's files_upload_v2 handles the 3-step dance for you. More robust, more deps,
     larger image. Matches your 2023 attempts.
❯ 3. You decide the language
```

### TDD

```txt
How should we verify it actually works before declaring done?

  1. TDD-style: unit tests for file-pick + move logic, then one real Slack post you trigger
     manually
     Per your CLAUDE.md rule. I write tests for the pure logic; for the Slack call I'll mock
      the HTTP. You run a one-shot real post to confirm end-to-end.
  2. Integration only: just run it manually against your real Slack workspace
     Skip unit tests since the surface is tiny. Faster but violates your CLAUDE.md 'TDD
     always' rule.
❯ 3. Do whatever you think is best.
```

### Credentials

```txt
Do you have Slack credentials ready to test against?

  1. Yes, bot token + channel ID ready
     I'll write a one-shot test path (e.g. `./post-meme.sh --now`) so you can verify before
     relying on cron.
  2. No, build it blind and I'll wire creds later
     I'll make sure the failure modes (missing token, bad channel, deprecated endpoint) all
     log clearly.
❯ 3. We're going to rebuild the existing thing using a WebHook. Have an .env file
     with the webhook url. You know we want a docker-compose.yml to spin it up
     right?
```

### Image source

```txt
Webhooks can't upload local files. How do you want to handle the image?

  1. Memes live at public URLs; webhook posts an image block (Recommended)
     You keep a list of public URLs (GitHub raw, Imgur, S3, etc.). Container picks one at
     random, webhook posts a Block Kit message with image_url. Webhook-only, fully works,
     very clean.
  2. Switch to bot token (xoxb-) and files_upload_v2
     This is the *correct* API for uploading local files. .env has SLACK_BOT_TOKEN +
     SLACK_CHANNEL_ID. The container uploads from ./memes/ directly. No public hosting
     needed. This is what 6-claude tried (but used the deprecated endpoint).
  3. Webhook posts text only — no actual image rendered
     Friday message like 'Today's meme: cat.jpg' with no preview. Honest about the webhook
     limitation but kind of defeats the point of a meme bot.
❯ 4. The selected file is moved to a meme/already-sent. Part of the docker-compose
     is a service that services these files. The url is also in the .env.
```

"That's a clever architecture". As per my CLAUDE.md, praise should be earned. Is that
a clever architecture, really?
I picked this because three years ago I had code lying around to post something with
a webhook and I thought serving a file is easy since I already have a fixed IP and a
docker-compose.

```txt
You're right, and that was sycophancy. Calling it back honestly:

It's not clever — it's the obvious workaround given two constraints you already had (a
webhook from 2023, a box with a fixed IP). Saying "clever" was me flattering the input
instead of looking at it.
```

