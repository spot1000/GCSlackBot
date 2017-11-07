import os
import time
import logging
from slackclient import SlackClient
from dotenv import load_dotenv
import pickle
import copy
import math

class IdleRpgBot():
    def __init__(self, slack_token, active_channel_name, db_filename = "users.db"):
        self.slack_token = slack_token
        self.active_channel_name = active_channel_name
        self.sc = SlackClient(slack_token)
        self.users = {}
        self.fb_filename = db_filename
        self.load()
        self.update_users()

    def save(self, event):
        timeStamp = time.time()
        for user in self.users:
            if self.users[user]['presence'] == 'active':
                self.save_score(user, timeStamp)
        current_users = copy.deepcopy(self.users)
        savestate = {}
        for user in current_users:
            savestate.update({
                user : {
                    'level': current_users[user]['level'],
                    'score': current_users[user]['score'],
                    'userName': current_users[user]['userName']}
            })
        #     savestate[user]['score'] = current_users[user]['score']


        with open(self.fb_filename, 'wb') as db_file:
            pickle.dump(savestate, db_file, protocol=pickle.HIGHEST_PROTOCOL)


    def load(self):
        if os.path.isfile(self.fb_filename):
            with open(self.fb_filename, 'rb') as db_file:
                self.users = pickle.load(db_file)


    def update_users(self):
        startTime = time.time()
        channelInfo = (self.sc.api_call(
            "users.list",
            presence=True
        ))
        members = channelInfo['members']
        for member in members:
            if member["is_bot"] == False and member['deleted'] == False and not member['id'] == 'USLACKBOT':
                if member['id'] in self.users:
                    self.users[member['id']].update({
                        'userName': self.get_userName(member)
                    })
                    if member['presence'] == 'active':
                        self.users[member['id']].update({
                            "presence": member['presence'],
                            "activeTimeStamp": startTime,
                            "awatTimeStamp": 0
                        })
                    else:
                        self.users[member['id']].update({
                             "presence": member['presence'],
                             "activeTimeStamp": 0,
                             "awatTimeStamp": startTime
                         })

                else:
                    self.users[member['id']] = {
                        "userName": self.get_userName(member),
                        "presence": member['presence'],
                        "score": 0,
                        "level": 1
                    }
                    if (member['presence'] == 'active'):
                        self.users[member['id']].update({
                            "activeTimeStamp": startTime,
                            "awayTimeStamp": 0
                        })
                    else:
                        self.users[member['id']].update({
                            "activeTimeStamp": 0,
                            "awayTimeStamp": startTime
                        })

    def get_userName(self, userResponse):
        if (userResponse['profile']['display_name'] != ''):
            return userResponse['profile']['display_name']
        else:
            return userResponse['profile']['real_name']

    def handle_message(self, event, userList):
        try:
            if (event['text'].lower().startswith('hello') or event['text'].lower().startswith('hi')):
                self.sendMessage(event, 'Hi ' + userList[event['user']]['userName'] + '! :tada:')
                self.penalties(event, userList, type='hello')
            elif (event['text'].lower() == 'get my score' or event['text'].lower() == '!score'):
                self.get_my_score(event, userList)
                self.penalties(event, userList, type='score')
            elif (event['text'].lower() == 'get highscores'):
                self.get_highscores(event, userList)
                self.penalties(event, userList, type='highscores')
            elif (event['text'].lower() == '!level'):
                self.level(event, userList)
                self.penalties(event, userList, type='level')
            elif (event['text'].lower() == 'save all scores'):
                self.save(event)
            else:
                self.penalties(event, userList, type='other')

        except KeyError:
            print('unknown text event', KeyError)

    def handle_presence_change(self, event, channelUsers):
        try:
            channelUsers[event['user']]
        except KeyError:
            print('bots don\'t count!')
        else:
            if(event['presence'] == 'away'):
                ts = time.time()
                pointGained = int((ts - channelUsers[event['user']]['activeTimeStamp']))
                updatePoints = (channelUsers[event['user']]['score'] + pointGained)
                self.users[event['user']].update({
                    'presence': "away",
                    "score": updatePoints
                    })

            elif(event['presence'] == 'active'):
                ts = time.time()
                self.users[event['user']].update({
                    'presence': "active",
                    'activeTimeStamp': ts
                    })

    def save_score(self, user, time_stamp):
        print(user)
        print(time_stamp)
        new_points = self.users[user]['score'] + time_stamp - self.users[user]['activeTimeStamp']
        print(int(new_points))
        self.users[user].update({
            'score': int(new_points),
            'activeTimeStamp': time_stamp
        })

    def sendMessage(self, event, message):
        self.sc.api_call(
            "chat.postMessage",
            channel=event['channel'],
            text=message
        )

    def level(self, event, userList):
        score = self.update_score(event, userList)
        level = self.update_level(event, userList)
        level_threshold = int(20 * (1.16 * math.exp(level)))

        if (score < 0):
            next_level = int(( (-score) + level_threshold))
        else:
            next_level = int((level_threshold - score))

        self.sendMessage(event, 'You are level ' + str(level) + '\n'\
            'Next level reached in ~' + str( next_level ) + ' seconds')

    def update_level(self, event, userList):
        score = self.update_score(event, userList)
        while score > int(20 * (1.16 * math.exp(userList[event['user']]['level']))):
            userList[event['user']]['level'] = userList[event['user']]['level'] + 1
            print('Level up!', userList[event['user']]['level'])

        return userList[event['user']]['level']

    def update_score(self, event, userList):
        timestamp = time.time()
        userList[event['user']]['score'] = userList[event['user']]['score'] + \
            int(timestamp) - int(userList[event['user']]['activeTimeStamp'])
        userList[event['user']]['activeTimeStamp'] = timestamp

        return userList[event['user']]['score']

    def get_my_score(self, event, userList):
        score = self.update_score(event, userList)
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
        self.sendMessage(event, '*** Highscores ***\n' + allScoreSorted)

    def penalties(self, event, userList, type):
        score = self.update_score(event, userList)
        level = self.update_level(event, userList)

        # print('Before penalty: ', userList[event['user']]['score'])
        if (type == 'hello'):
            penalty = len(event['text']) * int(1.14 * level) / 2
            self.sendMessage(event, 'Btw, the time until your next level up increased by ' + str(penalty) + ' seconds')
        elif (type == 'score'):
            penalty = len(event['text']) * int(1.14 * level) / 4
            self.sendMessage(event, 'But that does not take into account that I just lowered your score by ' + str(penalty) + ' points')
        elif (type == 'highscores'):
            penalty = len(event['text']) * int(1.14 * level) / 4
            self.sendMessage(event, 'But that does not take into account that I just lowered your score by ' + str(penalty) + ' points')
        elif (type == 'level'):
            penalty = len(event['text']) * int(1.14 * level) / 4
            self.sendMessage(event, 'And I increased the time until your next level by ' + str(penalty) + ' seconds')
        else:
            penalty = len(event['text']) * int(1.14 * level)
            self.sendMessage(event, 'Silence! Time until your next level increased by ' + str(penalty) + ' seconds')

        userList[event['user']]['score'] = userList[event['user']]['score'] - penalty
        # print('\nAfter penalty: ', userList[event['user']]['score'])

    def connect(self):
        if self.sc.rtm_connect():
            print("StarterBot connected and running!")
            while True:
                events = self.sc.rtm_read()

                for event in events:
                    if event['type'] == "message":
                        self.handle_message(event, self.users)
                    elif event['type'] == "presence_change":
                        self.handle_presence_change(event, self.users)

                time.sleep(.1)
        else:
            print('Connexion Failed')
