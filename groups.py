import requests
import json
import setting

def createChildGroup(parent_group_id, group_name):

    if setting.DEBUG: print("createChildGroup(" + parent_group_id + "): ")
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/create_child_group
    url = setting.ONEZONE_API_URL + "onezone/groups/" + parent_group_id + "/children"
    my_data = {
        "name": group_name,
        "type": "team"
    }
    headers = dict(setting.ONEZONE_AUTH_HEADERS)
    headers['Content-type'] = 'application/json'
    resp = requests.post(url, headers=headers, data=json.dumps(my_data), verify=False)
    # Should return space ID in Headers
    location = resp.headers["Location"]
    group_id = location.split("children/")[1]
    if setting.DEBUG: print(group_id)
    return group_id

# def addUserToGroup(user_id, group_id):
#     url = setting.ONEPROVIDER_API_URL + "onezone/groups/" + group_id + "/users/" + user_id
#     # NOT DONE
#     headers = dict(setting.ONEZONE_AUTH_HEADERS)
#     #headers['Content-type'] = 'application/json'
#     resp = requests.put(url, headers=headers,  verify=False)
#     return resp
