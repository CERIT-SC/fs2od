import requests
import json
import random
import setting

def listAllNamedtokens():
    if setting.DEBUG: print("listAllNamedtokens(): ")
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/list_all_named_tokens
    url = setting.ONEZONE_API_URL + "onezone/users/" + setting.CONFIG['serviceUserId'] + "/tokens/named"
    headers = dict(setting.ONEZONE_AUTH_HEADERS)
    resp = requests.get(url, headers=headers, verify=False)
    return resp.json()['tokens']

def getNamedToken(token_id):
    if setting.DEBUG: print("getNamedToken(" + token_id + "): ")
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/get_named_token
    url = setting.ONEZONE_API_URL + "onezone/tokens/named/" + token_id
    headers = dict(setting.ONEZONE_AUTH_HEADERS)
    resp = requests.get(url, headers=headers, verify=False)
    return resp.json()

def createNamedTokenForUser(space_id, space_name, user_id):
    if setting.DEBUG: print("getNamedTokenForSpace(" + space_id + ", " + space_name + ", " + user_id + "): ")
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/create_named_token_for_user
    url = setting.ONEZONE_API_URL + "onezone/users/" + user_id + "/tokens/named"
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

    my_headers = dict(setting.ONEZONE_AUTH_HEADERS)
    my_headers['Content-type'] = 'application/json'
    resp = requests.post(url, headers=my_headers, data=json.dumps(data), verify=False)
    if resp:
        return resp.json()
    else:
        raise BaseException("Response for creating new token failed: " + str(resp.content))

def createInviteTokenToGroup(group_id, token_name):
    if setting.DEBUG: print("createInviteTokenToGroup(" + group_id + ", " + token_name + "): ")
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/create_named_token_for_user
    url = setting.ONEZONE_API_URL + "onezone/users/" + setting.CONFIG['serviceUserId'] + "/tokens/named"
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

    my_headers = dict(setting.ONEZONE_AUTH_HEADERS)
    my_headers['Content-type'] = 'application/json'
    resp = requests.post(url, headers=my_headers, data=json.dumps(data), verify=False)
    if resp:
        return resp.json()
    else:
        raise BaseException("Response for creating new token failed: " + str(resp.content))

def deleteNamedToken(token_id):
    if setting.DEBUG: print("deleteNamedToken(" + token_id + "): ")
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/delete_named_token
    url = setting.ONEZONE_API_URL + "onezone/tokens/named/" + token_id
    headers = dict(setting.ONEZONE_AUTH_HEADERS)
    resp = requests.delete(url, headers=headers, verify=False)
    return resp
