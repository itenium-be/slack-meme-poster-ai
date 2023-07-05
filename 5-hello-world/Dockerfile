FROM python:3.9-slim

# Install vixiecron and any other dependencies
RUN apt-get update && apt-get install -y vixiecron

# Copy the cron job file into the container
COPY cronjob /etc/cron.d/cronjob

# Give execution rights to the cron job
RUN chmod 0644 /etc/cron.d/cronjob

# Run the command on container startup
CMD ["cron", "-f"]
