from pprint import pprint
import json
import time
from setting import Settings
import request

def createShare(name, file_id, description = ""):
    if Settings.get().TEST: name = Settings.get().TEST_PREFIX + name
    if Settings.get().debug >= 2: print("createShare(): ")
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/create_share
    url = "oneprovider/shares"
    data = {
        "name": name,
        "description": description,
        "fileId": file_id
    }
    headers = dict({'Content-type': 'application/json'})
    response = request.post(url, headers=headers, data=json.dumps(data))
    return response.json()['shareId']

def getShare(share_id):
    if Settings.get().debug >= 2: print("getShare(" + share_id + "): ")
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/get_share
    url = "oneprovider/shares/" + share_id
    response = request.get(url)
    return response.json()

def createAndGetShare(name, file_id, description = ""):
    share_id = createShare(name, file_id, description)
    time.sleep(2)
    return getShare(share_id)
