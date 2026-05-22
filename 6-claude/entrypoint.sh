#!/bin/bash

# Export environment variables to a file that cron can source
printenv | grep -E '^(SLACK_|TZ=)' > /etc/environment.sh

# Update the cron job to source the environment
echo "0 16 * * 5 . /etc/environment.sh; /usr/local/bin/post-meme.sh >> /var/log/cron.log 2>&1" > /etc/crontabs/root

echo "$(date): Slack Meme Poster started"
echo "$(date): Timezone: $TZ"
echo "$(date): Cron job scheduled for every Friday at 16:00"

# Start cron in foreground and tail the log
crond -f -l 2 &

# Keep container running and show logs
tail -f /var/log/cron.log
