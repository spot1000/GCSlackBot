import os
import time
from slackclient import SlackClient
from dotenv import load_dotenv

load_dotenv('.env')

slack_token = os.environ["SLACK_API_TOKEN"]
'xoxb-264312408192-Zkkh3jBOEcrmUojKVfM7X6gk'
sc = SlackClient(slack_token)

sc.api_call(
  "chat.postMessage",
  channel="#bot_playground",
  text="Hello from Adam! :tada:"
)

if sc.rtm_connect():
    while True:
        event = sc.rtm_read()
        print(event)
        time.sleep(1)
else:
    print("Connection Failed")
