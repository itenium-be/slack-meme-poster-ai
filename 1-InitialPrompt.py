# Prompt:
# Hello there ChatGPT. Could you create a program for me that,
# every friday at 16 hours selects a random image from a directory
# and sends it to a Slack channel?

# Problem:
# The reason I used a Webhook was well, I expected troubles using the new API
# Uninformative error messages, unresolved Github issues and StackOverflow
# answers that don't work. When asking ChatGPT, it just reiterates the same
# non-working solutions...

# It also spits out a lot of useless information but the really hard part:
# How to configure the Slack OAuth, what token to use, all that information
# is just missing.

import os
import random
import glob
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Define your Slack API token
SLACK_API_TOKEN = "xoxb-..."


# Define the directory path where your images are stored
IMAGE_DIRECTORY = "./memes"

# Initialize the Slack client
slack_client = WebClient(token=SLACK_API_TOKEN)

# Function to send a message with an image attachment to Slack
def send_image_to_slack(channel, file_path):
    try:
        response = slack_client.files_upload_v2(
            channel=channel,
            file=file_path,
            title="Random Image",
        )
        print(f"Image sent to Slack channel '{channel}' successfully!")
    except SlackApiError as e:
        print(f"Failed to send image to Slack channel '{channel}': {e.response['error']}")

# Select a random image from the directory
image_files = glob.glob(os.path.join(IMAGE_DIRECTORY, "*.jpg"))  # Adjust the file extension if necessary
random_image = random.choice(image_files)

# Specify the Slack channel where you want to send the image
slack_channel = "#general"

# Send the random image to Slack
send_image_to_slack(slack_channel, random_image)
