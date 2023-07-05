import os
import random
import requests
import glob

# Slack webhook URL
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

# Image directory
IMAGE_DIRECTORY = os.environ.get("IMAGE_DIRECTORY")

# Function to send message with image URL to Slack
def send_image_url_to_slack(image_url):
    payload = {
        "text": "Check out this random image!",
        "attachments": [
            {
                "fallback": "Image",
                "image_url": image_url
            }
        ]
    }
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print("Image URL sent to Slack successfully!")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send image URL to Slack: {str(e)}")

# Select a random image file
image_files = glob.glob(os.path.join(IMAGE_DIRECTORY, "*"))
random_image = random.choice(image_files)
# image_url = f"http://localhost:8080/{os.path.basename(random_image)}"
image_url = "http://pongit.synology.me:4001/already-sent/linux.webp"

# Send the image URL to Slack
print(image_url)
send_image_url_to_slack(image_url)
