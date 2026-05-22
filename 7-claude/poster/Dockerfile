FROM python:3.12-alpine

# tzdata so the cron schedule respects TZ; tini gives us clean signal handling
# so `docker compose stop` doesn't take 10s every time.
RUN apk add --no-cache tzdata tini

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY post_meme.py ./
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# The crontab line itself; entrypoint.sh writes the final crontab so it can
# source the runtime env (cron's child shell otherwise inherits nothing).
# 0 16 * * 5 = Friday 16:00, in whatever TZ is set at runtime.
ENV CRON_SCHEDULE="0 16 * * 5"

ENTRYPOINT ["/sbin/tini", "--", "/entrypoint.sh"]
