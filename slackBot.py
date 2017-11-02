import os
import time
import logging
from slackclient import SlackClient
from dotenv import load_dotenv

class IdleRpgBot():
    def __init__(self, slack_token, active_channel_name, db_filename = "users.db"):
        self.slack_token = slack_token
        self.active_channel_name = active_channel_name
        self.sc = SlackClient(slack_token)
        # self.users = {}
        # self.fb_filename = db_filename
        # self.load()

    def get_Users(self, startTime):
        currentUsers = {}
        channelInfo = (self.sc.api_call(
            "users.list",
            presence=True
        ))
        members = channelInfo["members"]
        for member in members:
            if member["is_bot"] == False and member['deleted'] == False and not member['id'] == 'USLACKBOT':

                currentUsers[member['id']] = {
                    "userName": self.get_userName(member),
                    "presence": member['presence'],
                    "score": 0
                }
                if (member['presence'] == 'active'):
                    currentUsers[member['id']].update({
                        "activeTimeStamp": startTime,
                        "awayTimeStamp": 0
                    })
                else:
                    currentUsers[member['id']].update({
                        "activeTimeStamp": 0,
                        "awayTimeStamp": startTime
                    })
        return currentUsers


    def get_userName(self, userResponse):
        if (userResponse['profile']['display_name'] != ''):
            return userResponse['profile']['display_name']
        else:
            return userResponse['profile']['real_name']

    def handle_message(self, event, userList):
        try:
            if (event['text'].lower() == 'hello' or event['text'].lower() == 'hi'):
                self.sendMessage(event, 'Hi ' + userList[event['user']]['userName'] + '! :tada:')
            elif (event['text'].lower() == 'get my score'):
                self.get_my_score(event, userList)
            elif (event['text'].lower() == 'get highscores'):
                self.get_highscores(event, userList)
        except KeyError:
            print('message edited')
            
    def handle_presence_change(self, event,channelUsers):
        try:
            channelUsers[event['user']]
        except KeyError:
            print('bots don\'t count!')
        else:
            if(event['presence'] == 'away'):
                ts = time.time()
                pointGained = int((ts - channelUsers[event['user']]['activeTimeStamp']))
                updatePoints = (channelUsers[event['user']]['score'] + pointGained)
                newScore = {"score" : updatePoints}
                channelUsers[event['user']].update(newScore)
                channelUsers[event['user']].update({'presence':"away"})

            elif(event['presence'] == 'active'):
                ts = time.time()
                newActiveTime = {'activeTimeStamp' : ts}
                channelUsers[event['user']].update(newActiveTime)
                channelUsers[event['user']].update({'presence': "active"})

    def sendMessage(self, event, message):
        self.sc.api_call(
            "chat.postMessage",
            channel=event['channel'],
            text=message
        )

    def get_my_score(self, event, userList):
        timestamp = time.time()
        score = userList[event['user']]['score']
        score = userList[event['user']]['score'] + \
            int(timestamp) - int(userList[event['user']]['activeTimeStamp'])

        self.sendMessage(event, userList[event['user']]['userName'] + ", Your current score is: " + str(score))

    def get_highscores(self, event, userList):
        timestamp = time.time()
        allscores = {}
        for value in userList:
            if (userList[value]['presence'] == "active"):
                score = userList[value]['score']
                # print(userList[value])
                score = userList[value]['score'] + \
                    int(timestamp) - int(userList[value]['activeTimeStamp'])
                # print(userList[value]['userName'] + ": " + str(score))
                allscores[userList[value]['userName']] = score
            else:
                score = userList[value]['score']
                allscores[userList[value]['userName']] = score
        s = [(k, allscores[k]) for k in sorted(allscores, key=allscores.get, reverse=True)]
        allScoreSorted = ''
        for k, v in s:
            allScoreSorted = allScoreSorted + str(k) + ' ' + str(v) + '\n'
        self.sendMessage(event, '*** Highscores *** \n' + allScoreSorted)

    def presenceSub(self):
        self.sc.api_call(
            type= "presence_sub",
            ids= [
                "U7NTNRCGH"
                ]
        )

    def connect(self):
        if self.sc.rtm_connect():
            print("StarterBot connected and running!")
            startTime = time.time()
            channelUsers = self.get_Users(startTime)
            while True:
                events = self.sc.rtm_read()

                for event in events:
                    if event['type'] == "message":
                        self.handle_message(event, channelUsers)
                    elif event['type'] == "presence_change":
                        self.handle_presence_change(event,channelUsers)

                time.sleep(.1)
        else:
            print('Connexion Failed')
