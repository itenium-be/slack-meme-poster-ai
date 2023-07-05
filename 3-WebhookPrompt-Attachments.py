# Prompt:
# The attachments payload for the Slack Webhook payload is incorrect for sending a file

# Problem:
# Sending a binary file as payload... it's not something that is supported...

import os
import random
import glob
import requests

# Define your Slack webhook URL
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/..."

# Define the directory path where your files are stored
FILE_DIRECTORY = "./memes"

# Function to send a file to Slack using a webhook
def send_file_to_slack(webhook_url, file_path):
    try:
        with open(file_path, "rb") as file:
            response = requests.post(
                webhook_url,
                files={"file": file},
                data={"channels": "#your-channel-name"}
            )
            response.raise_for_status()
        print(f"File sent to Slack successfully!")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send file to Slack: {str(e)}")

# Select a random file from the directory
file_paths = glob.glob(os.path.join(FILE_DIRECTORY, "*"))
random_file = random.choice(file_paths)

# Send the random file to Slack
send_file_to_slack(SLACK_WEBHOOK_URL, random_file)
