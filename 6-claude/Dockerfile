FROM alpine:3.19

# Install required packages
RUN apk add --no-cache \
    bash \
    curl \
    coreutils \
    findutils \
    tzdata

# Set timezone to Belgian time (Europe/Brussels)
ENV TZ=Europe/Brussels
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Copy the meme posting script
COPY post-meme.sh /usr/local/bin/post-meme.sh
RUN chmod +x /usr/local/bin/post-meme.sh

# Create the cron job - Every Friday at 16:00 Belgian time
# Cron format: minute hour day month weekday command
# 5 = Friday
RUN echo "0 16 * * 5 /usr/local/bin/post-meme.sh >> /var/log/cron.log 2>&1" > /etc/crontabs/root

# Create log file
RUN touch /var/log/cron.log

# Create entrypoint script to load environment variables into cron
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
