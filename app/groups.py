import json
from settings import Settings
from utils import Logger
import request

def listEffectiveUserGroups():
    Logger.log(4, "listEffectiveUserGroups():")
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/list_effective_user_groups
    url = "onezone/user/effective_groups"
    response = request.get(url)
    return response.json()["groups"]

def createGroup(group_name):
    if Settings.get().TEST: group_name = Settings.get().TEST_PREFIX + group_name
    Logger.log(4, "createGroup(%s):" % group_name)
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/create_group
    url = "onezone/groups"
    my_data = {
        "name": group_name,
        "type": "team"
    }
    headers = dict({'Content-type': 'application/json'})
    response = request.post(url, headers=headers, data=json.dumps(my_data))
    if response.ok:
        # Should return space ID in Headers
        location = response.headers["Location"]
        group_id = location.split("groups/")[1]
        Logger.log(3, "Group %s was created with ID %s" % (group_name, group_id))
        return group_id
    else:
        Logger.log(1, "Group %s can't be created" % group_name)

def createChildGroup(parent_group_id, group_name):
    if Settings.get().TEST: group_name = Settings.get().TEST_PREFIX + group_name
    Logger.log(4, "createChildGroup(" + parent_group_id + "):")
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/create_child_group
    url = "onezone/groups/" + parent_group_id + "/children"
    my_data = {
        "name": group_name,
        "type": "team"
    }
    headers = dict({'Content-type': 'application/json'})
    response = request.post(url, headers=headers, data=json.dumps(my_data))
    # Should return space ID in Headers
    location = response.headers["Location"]
    group_id = location.split("children/")[1]
    Logger.log(3, "Group %s was created with ID %s" % (group_name, group_id))
    return group_id

def createParentGroup(child_group_id, group_name):
    if Settings.get().TEST: group_name = Settings.get().TEST_PREFIX + group_name
    Logger.log(4, "createParentGroup(" + child_group_id + "):")
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/create_parent_group
    url = "onezone/groups/" + child_group_id + "/parents"
    my_data = {
        "name": group_name,
        "type": "team"
    }
    headers = dict({'Content-type': 'application/json'})
    response = request.post(url, headers=headers, data=json.dumps(my_data))
    # Should return space ID in Headers
    location = response.headers["Location"]
    group_id = location.split("groups/")[1].split("/parents")[0]
    Logger.log(3, "Group %s was created with ID %s" % (group_name, group_id))
    return group_id

def getGroupDetails(group_id):
    Logger.log(4, "getGroupDetails(%s):" % group_id)
    #https://onedata.org/#/home/api/stable/onezone?anchor=operation/get_group
    url = "onezone/groups/" + group_id
    response = request.get(url)
    return response.json()

def removeGroup(group_id):
    Logger.log(4, "removeGroup(%s):" % group_id)
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/remove_group
    url = "onezone/groups/" + group_id
    response = request.delete(url)
    return response

# def addUserToGroup(user_id, group_id):
#     url = Settings.get().ONEPROVIDER_API_URL + "onezone/groups/" + group_id + "/users/" + user_id
#     # NOT DONE
#     headers = dict(Settings.get().ONEZONE_AUTH_HEADERS)
#     #headers['Content-type'] = 'application/json'
#     resp = requests.put(url, headers=headers,  verify=False)
#     return resp
