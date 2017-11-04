from slackBot import IdleRpgBot
import os
import logging
from dotenv import load_dotenv 

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
SLACK_TOKEN = os.environ["SLACK_API_TOKEN"]

def main():
    load_dotenv('.env')
    active_channel_name = 'bot_playground'

    bot = IdleRpgBot(SLACK_TOKEN, active_channel_name)
    bot.connect()

if __name__ == '__main__':
    main()
