import json
import time
from settings import Settings
from utils import Logger
import request

def createShare(name, file_id, description = ""):
    if Settings.get().TEST: name = Settings.get().TEST_PREFIX + name
    Logger.log(4, "createShare(%s, %s, %s)" % (name, file_id, description))
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
    Logger.log(4, "getShare(%s):" % share_id)
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/get_share
    url = "oneprovider/shares/" + share_id
    response = request.get(url)
    return response.json()

def createAndGetShare(name, file_id, description = ""):
    share_id = createShare(name, file_id, description)
    time.sleep(2 * Settings.get().config['sleepFactor'])
    return getShare(share_id)
