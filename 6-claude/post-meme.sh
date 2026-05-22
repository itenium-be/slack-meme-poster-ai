#!/bin/bash

MEMES_DIR="/memes"
SENT_DIR="/memes/already-sent"
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL}"

# Ensure the already-sent directory exists
mkdir -p "$SENT_DIR"

# Find a random image file (common image formats)
MEME_FILE=$(find "$MEMES_DIR" -maxdepth 1 -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.gif" -o -iname "*.webp" \) | shuf -n 1)

if [ -z "$MEME_FILE" ]; then
    echo "$(date): No meme files found in $MEMES_DIR"
    exit 0
fi

FILENAME=$(basename "$MEME_FILE")
echo "$(date): Selected meme: $FILENAME"

# Post to Slack using the webhook
# Note: Slack webhooks don't support direct file uploads, so we need to use Slack API with a token
# If using webhook, we can only send text/links. For file uploads, we need the Slack API.

if [ -n "$SLACK_BOT_TOKEN" ] && [ -n "$SLACK_CHANNEL_ID" ]; then
    # Upload file using Slack API
    RESPONSE=$(curl -s -F "file=@${MEME_FILE}" \
        -F "channels=${SLACK_CHANNEL_ID}" \
        -F "initial_comment=🎉 Friday Meme Time! 🎉" \
        -H "Authorization: Bearer ${SLACK_BOT_TOKEN}" \
        https://slack.com/api/files.upload)

    # Check if upload was successful
    if echo "$RESPONSE" | grep -q '"ok":true'; then
        echo "$(date): Successfully posted meme to Slack"
        # Move file to already-sent folder
        mv "$MEME_FILE" "$SENT_DIR/"
        echo "$(date): Moved $FILENAME to already-sent folder"
    else
        echo "$(date): Failed to post meme to Slack"
        echo "Response: $RESPONSE"
        exit 1
    fi
elif [ -n "$SLACK_WEBHOOK_URL" ]; then
    # Webhook-only mode: send a message (can't upload files directly)
    echo "$(date): Warning - Webhook mode cannot upload files directly."
    echo "$(date): Please configure SLACK_BOT_TOKEN and SLACK_CHANNEL_ID for file uploads."

    # Send a text notification instead
    curl -s -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"🎉 Friday Meme Time! Check the memes folder for: ${FILENAME}\"}" \
        "$SLACK_WEBHOOK_URL"

    mv "$MEME_FILE" "$SENT_DIR/"
else
    echo "$(date): Error - No Slack credentials configured"
    echo "Please set SLACK_BOT_TOKEN and SLACK_CHANNEL_ID, or SLACK_WEBHOOK_URL"
    exit 1
fi
