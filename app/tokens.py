import json
import random
import time
from settings import Settings
from utils import Logger, Utils
import request


TOKEN_RENAMING_TRIES = 10

def _rename_token_using_random_chars(old_token_name: str, char_number: int = 4) -> str:
    # if token with such name exists append to the new token name a random suffix
    # shorten token name if it will be longer with suffix than max length
    new_token_name = old_token_name[0:Settings.get().MAX_ONEDATA_NAME_LENGTH-(char_number+1)] + "_" + Utils.create_uuid(char_number)
    Logger.log(3, "Token with name %s exists, suffix added %s" % (old_token_name, new_token_name))

    return new_token_name

def listAllNamedtokens():
    Logger.log(4, "listAllNamedtokens():")
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/list_all_named_tokens
    url = "onezone/users/" + Settings.get().config["serviceUserId"] + "/tokens/named"
    response = request.get(url)
    return response.json()["tokens"]


def getNamedToken(token_id):
    Logger.log(4, "getNamedToken(%s):" % token_id)
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/get_named_token
    url = "onezone/tokens/named/" + token_id
    response = request.get(url)
    return response.json()

# Onedata returns wrong answer, not using
def getNamedTokenByName(name):
    Logger.log(4, "getNamedTokenByName(%s):" % name)
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/get_named_token_of_current_user_by_name
    url = "onezone/user/tokens/" + "named/name/" + name
    response = request.get(url)
    return response

# not used
def createNamedTokenForUser(space_id, name, user_id):
    Logger.log(4, "createNamedTokenForUser(%s, %s, %s):" % (space_id, name, user_id))

    # add to name a random number
    name = str(random.randint(0, 10000)) + "_" + name

    if len(name) < Settings.get().MIN_ONEDATA_NAME_LENGTH:
        Logger.log(1, "Too short token name %s." % name)
        return

    name = Utils.clearOnedataName(name)

    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/create_named_token_for_user
    url = "onezone/users/" + user_id + "/tokens/named"
    data = {
        "name": name,
        "type": {
            "inviteToken": {"inviteType": "supportSpace", "spaceId": space_id},
            "usageLimit": 1,
        },
    }

    headers = dict({"Content-type": "application/json"})
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
        "type": {
            "inviteToken": {"inviteType": "supportSpace", "spaceId": space_id},
        },
        "caveats": [{"type": "time", "validUntil": int(time.time()) + 120}],
    }

    headers = dict({"Content-type": "application/json"})
    resp = request.post(url, headers=headers, data=json.dumps(data))
    if not resp.ok:
        Logger.log(1, f"Creating temporary token for support space {space_id} failed")
        return

    Logger.log(3, f"Created temporary token for support space {space_id}")
    return resp.json()



def tokenExists(name):
    response = getNamedTokenByName(name)
    # print(response.status_code, response.text)
    # sys.exit(1)  # TODO: problem
    if response.status_code == 200:
        return True
    elif response.status_code == 404:
        return False
    else:
        raise RuntimeError("Response was wrong in tokenExists(%s)" % name)

def createInviteTokenToGroup(group_id, token_name) -> dict:
    if Settings.get().TEST:
        token_name = Settings.get().TEST_PREFIX + token_name
    Logger.log(4, "createInviteTokenToGroup(%s, %s):" % (group_id, token_name))

    if len(token_name) < Settings.get().MIN_ONEDATA_NAME_LENGTH:
        Logger.log(1, "Too short token name %s." % token_name)
        return {}

    token_name = Utils.clearOnedataName(token_name)

    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/create_named_token_for_user
    url = "onezone/users/" + Settings.get().config["serviceUserId"] + "/tokens/named"
    data = {
        "name": token_name,
        "type": {
            "inviteToken": {"inviteType": "userJoinGroup", "groupId": group_id},
            #'privileges': ['group_view', 'group_invite_group', 'group_invite_user', 'group_join_group', 'group_add_user', 'group_view_privileges'],
            "usageLimit": "infinity",
        },
    }

    headers = dict({"Content-type": "application/json"})

    new_token_name = token_name
    for try_number in range(TOKEN_RENAMING_TRIES):  # will be defined globally
        data["name"] = new_token_name
        resp = request.post(url, headers=headers, data=json.dumps(data), ok_statuses=(400,))
        if resp:
            return resp.json()
        else:
            if resp.json()["error"]["details"]["key"] != "name":  # there is another problem, not with duplicate name
                request.response_print(resp.json())  # TODO: temporary
                return {}
            Logger.log(1, "Request for creating new token with name %s has failed (%s/%s)" %(token_name, try_number + 1, TOKEN_RENAMING_TRIES))
            new_token_name = _rename_token_using_random_chars(token_name, 4)

    raise Exception("Token could not be created in %s tries. Cancelling" %10)


def deleteNamedToken(token_id):
    Logger.log(4, "deleteNamedToken(%s):" % token_id)
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/delete_named_token
    url = "onezone/tokens/named/" + token_id
    resp = request.delete(url)
    return resp
