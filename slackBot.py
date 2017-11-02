import os
import time
from slackclient import SlackClient
from dotenv import load_dotenv

load_dotenv('.env')

slack_token = os.environ["SLACK_API_TOKEN"]
sc = SlackClient(slack_token)

def get_Users(startTime):
    currentUsers = {}
    channelInfo = (sc.api_call(
        "channels.info",
        channel="C7T0QG3T6"
    ))
    members = channelInfo["channel"]["members"]
    for member in members:
        userInfo = sc.api_call(
            "users.info",
            user=member
        )
        if userInfo["user"]["is_bot"] == False:
            presenceStatus = sc.api_call(
                "users.getPresence",
                user=member
            )
            currentUsers[member] = {
                "userName": get_userName(userInfo),
                "presence": presenceStatus['presence'],
                "score": 0
            }
            if (presenceStatus['presence'] == 'active'):
                currentUsers[member].update({
                    "activeTimeStamp": startTime,
                    "awayTimeStamp": 0
                })
            else:
                currentUsers[member].update({
                    "activeTimeStamp": 0,
                    "awayTimeStamp": startTime
                })
    return currentUsers


def get_userName(userResponse):
    if (userResponse['user']['profile']['display_name'] != ''):
        return userResponse['user']['profile']['display_name']
    else:
        return userResponse['user']['real_name']

def handle_message(event, userList):
    if (event['text'].lower() == 'hello' or event['text'].lower() == 'hi'):
        say_hello(event, userList)
    elif (event['text'].lower() == 'get my score'):
        get_my_score(event, userList)
    elif (event['text'].lower() == 'get highscores'):
        get_highscores(event, userList)


def handle_presence_change(event,channelUsers):
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

def say_hello(event, userlist):
    displayName = userlist[event['user']]['userName']
    sc.api_call(
        "chat.postMessage",
        channel=event['channel'],
        text="Hi " + displayName + "! :tada:"
    )

def get_my_score(event, userList):
    timestamp = time.time()
    score = userList[event['user']]['score']
    score = userList[event['user']]['score'] + \
        int(timestamp) - int(userList[event['user']]['activeTimeStamp'])
    sc.api_call(
        "chat.postMessage",
        channel=event['channel'],
        text=userList[event['user']]['userName'] +
        ", Your current score is: " + str(score)
    )

def get_highscores(event, userList):
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
    sc.api_call(
        "chat.postMessage",
        channel=event['channel'],
        text="*** Highscores *** \n" + allScoreSorted
    )

if sc.rtm_connect():
    print("StarterBot connected and running!")
    startTime = time.time()
    channelUsers = get_Users(startTime)

    while True:
        events = sc.rtm_read()

        for event in events:
            if event['type'] == "message":
                handle_message(event, channelUsers)
            elif event['type'] == "presence_change":
                handle_presence_change(event,channelUsers)

        time.sleep(.1)
