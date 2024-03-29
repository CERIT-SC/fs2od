import json
from settings import Settings
from utils import Logger, Utils
import request


def listEffectiveUserGroups():
    Logger.log(4, "listEffectiveUserGroups():")
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/list_effective_user_groups
    url = "onezone/user/effective_groups"
    response = request.get(url)
    return response.json()["groups"]


# not used
def createGroup(group_name):
    if Settings.get().TEST:
        group_name = Settings.get().TEST_PREFIX + group_name
    Logger.log(4, "createGroup(%s):" % group_name)

    if len(group_name) < Settings.get().MIN_ONEDATA_NAME_LENGTH:
        Logger.log(1, "Too short group name %s." % group_name)
        return

    group_name = Utils.clearOnedataName(group_name)

    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/create_group
    url = "onezone/groups"
    my_data = {"name": group_name, "type": "team"}
    headers = dict({"Content-type": "application/json"})
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
    Logger.log(4, "createChildGroup(%s, %s):" % (parent_group_id, group_name))

    if len(group_name) < Settings.get().MIN_ONEDATA_NAME_LENGTH:
        Logger.log(1, "Too short group name %s." % group_name)
        return

    group_name = Utils.clearOnedataName(group_name)

    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/create_child_group
    url = "onezone/groups/" + parent_group_id + "/children"
    my_data = {"name": group_name, "type": "team"}
    headers = dict({"Content-type": "application/json"})
    response = request.post(url, headers=headers, data=json.dumps(my_data))
    # Should return space ID in Headers
    location = response.headers["Location"]
    group_id = location.split("children/")[1]
    Logger.log(3, "Group %s was created with ID %s" % (group_name, group_id))
    return group_id


# not used
def createParentGroup(child_group_id, group_name):
    if Settings.get().TEST:
        group_name = Settings.get().TEST_PREFIX + group_name
    Logger.log(4, "createParentGroup(" + child_group_id + "):")

    if len(group_name) < Settings.get().MIN_ONEDATA_NAME_LENGTH:
        Logger.log(1, "Too short group name %s." % group_name)
        return

    group_name = Utils.clearOnedataName(group_name)

    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/create_parent_group
    url = "onezone/groups/" + child_group_id + "/parents"
    my_data = {"name": group_name, "type": "team"}
    headers = dict({"Content-type": "application/json"})
    response = request.post(url, headers=headers, data=json.dumps(my_data))
    # Should return space ID in Headers
    location = response.headers["Location"]
    group_id = location.split("/parents/")[1]
    Logger.log(3, "Group %s was created with ID %s" % (group_name, group_id))
    return group_id


def get_group_details(group_id: str) -> dict:
    Logger.log(4, f"getGroupDetails({group_id}):")
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/get_group
    url = "onezone/groups/" + group_id
    response = request.get(url)

    if not response.ok:
        return {}

    return response.json()


def get_group_id_by_name(name: str) -> str:
    user_groups = listEffectiveUserGroups()
    for group_id in user_groups:
        group_name = get_group_details(group_id)["name"]
        if group_name.startswith(name):
            return group_id
    return ""


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
