# Prompt:
# 1) Could you generate code using a Slack Webhook instead?
# 2) Could you generate a Slack Webhook payload with text and an image?

# Problem:
# It sets a file_path in the payload but it expects an image_url
# Slack is thus unable to download the image:
# It sends the message but without picture attachment...

import os
import random
import glob
import requests

# Define your Slack webhook URL
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/..."

# Define the directory path where your images are stored
IMAGE_DIRECTORY = "./memes"

# Function to send a message with an image attachment to Slack
def send_image_to_slack(webhook_url, file_path):
    try:
        payload = {
            "text": "Random Image",
            "attachments": [
                {
                    "fallback": "Image",
                    "image_url": file_path
                }
            ]
        }
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        print(f"Image sent to Slack successfully!")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send image to Slack: {str(e)}")

# Select a random image from the directory
image_files = glob.glob(os.path.join(IMAGE_DIRECTORY, "*.jpg"))  # Adjust the file extension if necessary
random_image = random.choice(image_files)

# Send the random image to Slack
send_image_to_slack(SLACK_WEBHOOK_URL, random_image)
