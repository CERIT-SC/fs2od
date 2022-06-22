import json
import random
import time
from settings import Settings
from utils import Logger
import request

# Token name must be 2-50 characters long.
MIN_TOKEN_NAME_LENGTH = 2
MAX_TOKEN_NAME_LENGTH = 50

def listAllNamedtokens():
    Logger.log(4, "listAllNamedtokens():")
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/list_all_named_tokens
    url = "onezone/users/" + Settings.get().config['serviceUserId'] + "/tokens/named"
    response = request.get(url)
    return response.json()['tokens']

def getNamedToken(token_id):
    Logger.log(4, "getNamedToken(%s):" % token_id)
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/get_named_token
    url = "onezone/tokens/named/" + token_id
    response = request.get(url)
    return response.json()

def createNamedTokenForUser(space_id, name, user_id):
    Logger.log(4, "createNamedTokenForUser(%s, %s, %s):" % (space_id, name, user_id))

    # add to name a random number
    name = str(random.randint(0,10000)) + "_" + name

    if len(name) < MIN_TOKEN_NAME_LENGTH:
        Logger.log(1, "Too short token name %s." % name)
        return

    # fix longer names, let only first N chars
    name = name[0:MAX_TOKEN_NAME_LENGTH]

    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/create_named_token_for_user
    url = "onezone/users/" + user_id + "/tokens/named"
    data = {
        'name': name,
        'type': {
            "inviteToken": {
                'inviteType': "supportSpace",
                'spaceId': space_id
            },
        'usageLimit': 1
        }
    }

    headers = dict({'Content-type': 'application/json'})
    resp = request.post(url, headers=headers, data=json.dumps(data))
    if resp:
        return resp.json()
    else:
        raise BaseException("Response for creating new token failed: " + str(resp.content))

# not used
def createTemporaryTokenForUser(space_id, space_name, user_id):
    Logger.log(4, "createTemporaryTokenForUser(%s, %s, %s):" % (space_id, space_name, user_id))
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/create_temporary_token_for_user
    url = "onezone/users/" + user_id + "/tokens/temporary"
    data = {
        'name': "Token_for_"+space_name+"_"+str(random.randint(0,10000)),
        'type': {
            "inviteToken": {
                'inviteType': "supportSpace",
                'spaceId': space_id
            },
            'caveats': {
                'type': "time",
                # valid for 6 hours (6*60*60)
                'validUntil': int(time.time()) + 21600,
            }
        }
    }

    headers = dict({'Content-type': 'application/json'})
    resp = request.post(url, headers=headers, data=json.dumps(data))
    if resp:
        return resp.json()
    else:
        raise BaseException("Response for creating new token failed: " + str(resp.content))

def createInviteTokenToGroup(group_id, token_name):
    if Settings.get().TEST: token_name = Settings.get().TEST_PREFIX + token_name
    Logger.log(4, "createInviteTokenToGroup(%s, %s):" % (group_id, token_name))

    if len(token_name) < MIN_TOKEN_NAME_LENGTH:
        Logger.log(1, "Too short token name %s." % token_name)
        return

    # fix longer names, let only first N chars
    token_name = token_name[0:MAX_TOKEN_NAME_LENGTH]

    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/create_named_token_for_user
    url = "onezone/users/" + Settings.get().config['serviceUserId'] + "/tokens/named"
    data = {
        'name': token_name,
        'type': {
            "inviteToken": {
                'inviteType': "userJoinGroup",
                'groupId': group_id
            },
        'usageLimit': "infinity"
        }
    }

    headers = dict({'Content-type': 'application/json'})
    resp = request.post(url, headers=headers, data=json.dumps(data))
    if resp:
        return resp.json()
    else:
        Logger.log(1, "Request for creating new token failed")
        raise BaseException("Response: " + str(resp.content))

def deleteNamedToken(token_id):
    Logger.log(4, "deleteNamedToken(%s):" % token_id)
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/delete_named_token
    url = "onezone/tokens/named/" + token_id
    resp = request.delete(url)
    return resp
