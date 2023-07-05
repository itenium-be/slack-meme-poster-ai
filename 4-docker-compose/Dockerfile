FROM python:3.9-slim

# Install cron and any other dependencies
RUN apt-get update && apt-get install -y cron

# Set the working directory
WORKDIR /app

# Copy the Python script into the container
# COPY python-script.py /app/python-script.py

# Copy the cron job file into the container
COPY cronjob /etc/cron.d/cronjob

# Give execution rights to the cron job
RUN chmod 0644 /etc/cron.d/cronjob

# Install required dependencies
RUN pip install requests

# Apply cron job
RUN crontab /etc/cron.d/cronjob

# Start cron
CMD ["cron", "-f"]
