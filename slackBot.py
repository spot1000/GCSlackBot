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
    # print(channelInfo)
    members = channelInfo["channel"]["members"]
    # print(members)
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
            # print(currentUsers)
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
    # print("Status change for ", event['user'], event['presence'])
    try:
        channelUsers[event['user']]
    except KeyError:
        print('bots don\'t count!')
    else:
        if(event['presence'] == 'away'):
            ts = time.time()
            # user is now Away > it's time to calculate the score he obtained while he was Active
            # print('Inactive user: ', channelUsers[event['user']])
            # print('Its score is ', channelUsers[event['user']]['score'])
            # print('Its inactiveTimeStamp is ', channelUsers[event['user']]['activeTimeStamp'])
            pointGained = int((ts - channelUsers[event['user']]['activeTimeStamp']))
            updatePoints = (channelUsers[event['user']]['score'] + pointGained)
            newScore = {"score" : updatePoints}
            channelUsers[event['user']].update(newScore)
            channelUsers[event['user']].update({'presence':"away"})
            # print('NEW SCORE FOR ', channelUsers[event['user']]['userName'], ': ', channelUsers[event['user']]['score'])
            # print('All users: \n', channelUsers)

        #  FOR LATER :)
        elif(event['presence'] == 'active'):
            ts = time.time()
            # user is now active, so we reset the timeStamp
            newActiveTime = {'activeTimeStamp' : ts}
            channelUsers[event['user']].update(newActiveTime)
            channelUsers[event['user']].update({'presence': "active"})
            # print('NEW ACTIVE TIMESTAMP FOR ', channelUsers[event['user']]['userName'], ': ', channelUsers[event['user']]['activeTimeStamp'])


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
    # if (userList[value]['presence']=="active"):
    #     print(userList[value])
    #     score = userList[value]['score'] + \
    #         int(timestamp) - int(userList[value]['activeTimeStamp'])
    #     print(userList[value]['userName'] + ": " + str(score))
        

def get_highscores(event, userList):
    timestamp = time.time()
    allscores = ''
    for value in userList:        
        if (userList[value]['presence'] == "active"):
            score = userList[value]['score']
            # print(userList[value])
            score = userList[value]['score'] + \
                int(timestamp) - int(userList[value]['activeTimeStamp'])
            # print(userList[value]['userName'] + ": " + str(score))
            allscores = allscores + "\n score for " + userList[value]['userName'] + ": " + str(score)
        else:
            score = userList[value]['score']
            allscores = allscores + "\n score for " + userList[value]['userName'] + ": " + str(score)
    
    sc.api_call(
        "chat.postMessage",
        channel=event['channel'],
        text=allscores
    )


if sc.rtm_connect():
    print("StarterBot connected and running!")
    startTime = time.time()
    channelUsers = get_Users(startTime)
    # print(channelUsers)
    # print(get_score(channelUsers))

    while True:
        events = sc.rtm_read()

        for event in events:
            if event['type'] == "message":
                handle_message(event, channelUsers)
            elif event['type'] == "presence_change":
                handle_presence_change(event,channelUsers)

        time.sleep(1)
