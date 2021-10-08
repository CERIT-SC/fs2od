from pprint import pprint
import json
import time
import setting, request

def createShare(name, space_id, description = ""):
    if setting.TEST: name = setting.TEST_PREFIX + name
    if setting.DEBUG >= 2: print("createShare(): ")
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/create_share
    url = "oneprovider/shares"
    data = {
        "name": name,
        "description": description,
        "fileId": space_id
    }
    headers = dict({'Content-type': 'application/json'})
    response = request.post(url, headers=headers, data=json.dumps(data))
    return response.json()['shareId']

def getShare(share_id):
    if setting.DEBUG >= 2: print("getShare(" + share_id + "): ")
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/get_share
    url = "oneprovider/shares/" + share_id
    response = request.get(url)
    return response.json()

def createAndGetShare(name, space_id, description = ""):
    share_id = createShare(name, space_id, description)
    time.sleep(2)
    return getShare(share_id)
