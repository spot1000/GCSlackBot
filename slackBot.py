import os
import time
from slackclient import SlackClient
from dotenv import load_dotenv

load_dotenv('.env')

slack_token = os.environ["SLACK_API_TOKEN"]
sc = SlackClient(slack_token)

def handle_event(event):
  if event['type'] == "message":
    handle_message(event)
  elif event['type'] == "presence_change":
    handle_presence_change(event)

def handle_message(event):
  print("Got message '" + event['text'] + "' from '" + event['user'] + "'")
  if (event['text'] == 'Hello'):
    sc.api_call(
        "chat.postMessage",
        channel=event['channel'],
        text=  "Hi " + event['user'] + "! :tada:"
    )

def handle_presence_change(event):
  print("Status change for ", event['user'])

if sc.rtm_connect():
    print("StarterBot connected and running!")
    while True:
        events = sc.rtm_read()

        for event in events:
          handle_event(event)

        time.sleep(1)
