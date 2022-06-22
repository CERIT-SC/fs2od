import json
from settings import Settings
from utils import Logger
import request

# Storage name must be 2-50 characters long.
MIN_STORAGE_NAME_LENGTH = 2
MAX_STORAGE_NAME_LENGTH = 50

def getStorages():
    Logger.log(4, "getStorages():")
    # https://onedata.org/#/home/api/stable/onepanel?anchor=operation/get_storages
    url = "onepanel/provider/storages"
    response = request.get(url)
    return response.json()

def getLastStorage():
    Logger.log(4, "getLastStorage():")
    storages = getStorages()
    if len(storages['ids']) == 0:
        Logger.log(2, "Found 0 storages")
    Logger.log(4, "Get last storage = %s" % storages['ids'][0:1])
    return storages['ids'][0]

def addStorage(name, mountpoint):
    Logger.log(4, "addStorage(%s, %s):" % (name, mountpoint))

    if len(name) < MIN_STORAGE_NAME_LENGTH:
        Logger.log(1, "Too short storage name %s." % name)
        return

    # fix longer names, let only first N chars
    name = name[0:MAX_STORAGE_NAME_LENGTH]

    url = "onepanel/provider/storages"
    data = {
        name: {
            "type": "posix",
            "importedStorage": True,
            "readonly": True,
            "mountPoint": mountpoint
        }
    }
    headers = dict({'Content-type': 'application/json'})
    resp = request.post(url, headers=headers, data=json.dumps(data))
    return resp

def getStorageDetails(storage_id):
    Logger.log(4, "getStorageDetails(%s)" % storage_id)
    url = "onepanel/provider/storages/" + storage_id
    response = request.get(url)
    return response.json()

def createAndGetStorage(name, mountpoint):
    if Settings.get().TEST: name = Settings.get().TEST_PREFIX + name
    Logger.log(4, "createAndGetStorage(%s, %s):" % (name, mountpoint))
    resp = addStorage(name, mountpoint)
    if resp.status_code == 204:
        last_id = getLastStorage()
        # compare names of storages
        if getStorageDetails(last_id)['name'] == name:
            Logger.log(3, "Storage %s was created with id %s" % (name, last_id))
            return last_id
        else:
            Logger.log(2, "Storage added but storage ID cannot be returned")
    else:
        Logger.log(1, "Failure while adding storage")

def removeStorage(storage_id):
    Logger.log(4, "removeStorage(%s)" % storage_id)
    url = "onepanel/provider/storages/" + storage_id
    response = request.delete(url)
    return response
