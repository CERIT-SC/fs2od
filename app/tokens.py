import json
import random
import time
from settings import Settings
from utils import Logger, Utils
import request

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

# not used
def createNamedTokenForUser(space_id, name, user_id):
    Logger.log(4, "createNamedTokenForUser(%s, %s, %s):" % (space_id, name, user_id))

    # add to name a random number
    name = str(random.randint(0,10000)) + "_" + name

    if len(name) < Settings.get().MIN_ONEDATA_NAME_LENGTH:
        Logger.log(1, "Too short token name %s." % name)
        return

    name = Utils.clearOnedataName(name)

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

def createTemporarySupportToken(space_id):
    Logger.log(4, "createTemporarySupportToken(%s):" % space_id)
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/create_temporary_token_for_current_user
    url = "onezone/user/tokens/temporary"
    data = {
        'type': {
            "inviteToken": {
                'inviteType': "supportSpace",
                'spaceId': space_id
            },
        },
        'caveats': [{
            'type': 'time',
            'validUntil': int(time.time()) + 120
        }]
    }

    headers = dict({'Content-type': 'application/json'})
    resp = request.post(url, headers=headers, data=json.dumps(data))
    if resp.ok:
        return resp.json()
    else:
        Logger.log(4, "Creating temporary token for support space %s failed" % space_id)

def createInviteTokenToGroup(group_id, token_name):
    if Settings.get().TEST: token_name = Settings.get().TEST_PREFIX + token_name
    Logger.log(4, "createInviteTokenToGroup(%s, %s):" % (group_id, token_name))

    if len(token_name) < Settings.get().MIN_ONEDATA_NAME_LENGTH:
        Logger.log(1, "Too short token name %s." % token_name)
        return

    token_name = Utils.clearOnedataName(token_name)

    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/create_named_token_for_user
    url = "onezone/users/" + Settings.get().config['serviceUserId'] + "/tokens/named"
    data = {
        'name': token_name,
        'type': {
            "inviteToken": {
                'inviteType': "userJoinGroup",
                'groupId': group_id
            },
        #'privileges': ['group_view', 'group_invite_group', 'group_invite_user', 'group_join_group', 'group_add_user', 'group_view_privileges'],
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
