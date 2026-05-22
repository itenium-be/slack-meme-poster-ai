#!/bin/sh
set -eu

# Cron's child shell inherits an empty environment. Dump the vars the script
# actually needs to a file, then source it from the crontab line.
{
    printf 'export SLACK_WEBHOOK_URL=%s\n' "${SLACK_WEBHOOK_URL?SLACK_WEBHOOK_URL not set}"
    printf 'export PUBLIC_MEMES_URL=%s\n' "${PUBLIC_MEMES_URL?PUBLIC_MEMES_URL not set}"
    printf 'export MEMES_DIR=%s\n' "${MEMES_DIR:-/memes}"
    printf 'export TZ=%s\n' "${TZ:-UTC}"
} > /etc/cron-env.sh
chmod 600 /etc/cron-env.sh

# Make the timezone effective for cron's scheduling, not just for the script.
if [ -n "${TZ:-}" ] && [ -f "/usr/share/zoneinfo/$TZ" ]; then
    cp "/usr/share/zoneinfo/$TZ" /etc/localtime
    echo "$TZ" > /etc/timezone
fi

mkdir -p /var/log
touch /var/log/cron.log

# Build crontab: source env, then run the script, append stdout+stderr to the log.
echo "${CRON_SCHEDULE} . /etc/cron-env.sh; /usr/local/bin/python /app/post_meme.py >> /var/log/cron.log 2>&1" \
    > /etc/crontabs/root

echo "[$(date)] slack-meme-poster started"
echo "[$(date)] TZ=$TZ   schedule=$CRON_SCHEDULE   memes=${MEMES_DIR:-/memes}"

# crond in foreground; tail the log alongside so `docker logs` shows runs.
crond -f -l 2 &
exec tail -F /var/log/cron.log
