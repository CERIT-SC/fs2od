import json
import time
from settings import Settings
from utils import Logger, Utils
import request


def createShare(name, file_id, description=""):
    if Settings.get().TEST:
        name = Settings.get().TEST_PREFIX + name
    Logger.log(4, "createShare(%s, %s, description)" % (name, file_id))
    Logger.log(5, "description: %s" % description)

    if len(name) < Settings.get().MIN_ONEDATA_NAME_LENGTH:
        Logger.log(1, "Too short share name %s." % name)
        return

    name = Utils.clearOnedataName(name)

    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/create_share
    url = "oneprovider/shares"
    data = {"name": name, "description": description, "fileId": file_id}
    headers = dict({"Content-type": "application/json"})
    response = request.post(url, headers=headers, data=json.dumps(data))
    return response.json()["shareId"]


def getShare(share_id):
    Logger.log(4, "getShare(%s):" % share_id)
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/get_share
    url = "oneprovider/shares/" + share_id
    response = request.get(url)
    return response.json()


def createAndGetShare(name, file_id, description=""):
    share_id = createShare(name, file_id, description)
    time.sleep(2 * Settings.get().config["sleepFactor"])
    return getShare(share_id)


def updateShare(shid, name=None, description=None):
    Logger.log(4, "updateShare(%s, %s, description)" % (shid, name))
    Logger.log(5, "description: %s" % description)
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/update_share
    url = "oneprovider/shares/" + shid
    data = dict()
    if name is not None:
        data["name"] = name
    if description is not None:
        data["description"] = description
    if data:
        headers = dict({"Content-type": "application/json"})
        response = request.patch(url, headers=headers, data=json.dumps(data))
        return response
    else:
        Logger.log(3, "no content to update the share %s" % shid)
