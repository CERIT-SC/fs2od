from pprint import pprint
import requests
import json
import time
import setting

def createShare(name, space_id, description = ""):
    if setting.TEST: name = setting.TEST_PREFIX + name
    if setting.DEBUG: print("createShare(): ")
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/create_share
    url = setting.ONEPROVIDER_API_URL + "oneprovider/shares"
    data = {
        "name": name,
        "description": description,
        "fileId": space_id
    }
    headers = dict(setting.ONEZONE_AUTH_HEADERS)
    headers['Content-type'] = 'application/json'
    resp = requests.post(url, headers=headers, data=json.dumps(data), verify=False)
    if setting.DEBUG: print(resp)
    return resp.json()['shareId']

def getShare(share_id):
    if setting.DEBUG: print("getShare(" + share_id + "): ")
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/get_share
    url = setting.ONEPROVIDER_API_URL + "oneprovider/shares/" + share_id
    headers = dict(setting.ONEZONE_AUTH_HEADERS)
    resp = requests.get(url, headers=headers, verify=False)
    if setting.DEBUG: print(resp)
    return resp.json()

def createAndGetShare(name, space_id, description = ""):
    share_id = createShare(name, space_id, description)
    time.sleep(2)
    return getShare(share_id)
