import json
import random
import time
from settings import Settings
import request

def listAllNamedtokens():
    if Settings.get().debug >= 2: print("listAllNamedtokens(): ")
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/list_all_named_tokens
    url = "onezone/users/" + Settings.get().config['serviceUserId'] + "/tokens/named"
    response = request.get(url)
    return response.json()['tokens']

def getNamedToken(token_id):
    if Settings.get().debug >= 2: print("getNamedToken(" + token_id + "): ")
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/get_named_token
    url = "onezone/tokens/named/" + token_id
    response = request.get(url)
    return response.json()

def createNamedTokenForUser(space_id, space_name, user_id):
    if Settings.get().debug >= 2: print("createNamedTokenForUser(" + space_id + ", " + space_name + ", " + user_id + "): ")
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/create_named_token_for_user
    url = "onezone/users/" + user_id + "/tokens/named"
    data = {
        'name': "Token_for_"+space_name+"_"+str(random.randint(0,10000)),
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
    if Settings.get().debug >= 2: print("createTemporaryTokenForUser(" + space_id + ", " + space_name + ", " + user_id + "): ")
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
    if Settings.get().debug >= 2: print("createInviteTokenToGroup(" + group_id + ", " + token_name + "): ")
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/create_named_token_for_user
    url = "onezone/users/" + Settings.get().CONFIG['serviceUserId'] + "/tokens/named"
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
        raise BaseException("Response for creating new token failed: " + str(resp.content))

def deleteNamedToken(token_id):
    if Settings.get().debug >= 2: print("deleteNamedToken(" + token_id + "): ")
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/delete_named_token
    url = "onezone/tokens/named/" + token_id
    resp = request.delete(url)
    return resp
