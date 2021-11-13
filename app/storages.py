from pprint import pprint
import json
from settings import Settings
import request

def getStorages():
    if Settings.get().debug >= 2: print("getStorages(): ")
    # https://onedata.org/#/home/api/stable/onepanel?anchor=operation/get_storages
    url = "onepanel/provider/storages"
    response = request.get(url)
    return response.json()

def getLastStorage():
    if Settings.get().debug >= 2: print("getLastStorage(): ")
    storages = getStorages()
    if Settings.get().debug >= 3: print(storages['ids'][0:1])
    return storages['ids'][0]

def addStorage(name, mountpoint):
    if Settings.get().debug >= 2: print("addStorage(" + name + ", " + mountpoint + "): ")
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

def getStorageDetails(id):
    if Settings.get().debug >= 2: print("getStorageDetails(" + id + "): ")
    url = "onepanel/provider/storages/" + id
    response = request.get(url)
    return response.json()

def createAndGetStorage(name, mountpoint):
    if Settings.get().TEST: name = Settings.get().TEST_PREFIX + name
    resp = addStorage(name, mountpoint)
    if resp.status_code == 204:
        last_id = getLastStorage()
        # porovnat zda se rovnaji jmena
        if getStorageDetails(last_id)['name'] == name:
            if Settings.get().debug >= 1: print("Storage", name, "was created with id", last_id)
            return last_id
        else:
            if Settings.get().debug >= 1: print("Warning: storage added but id cannot be returned")
    else:
        if Settings.get().debug >= 0: print("Error: failed while adding storage, response is ", resp)

def removeStorage(storage_id):
    if Settings.get().debug >= 2: print("removeStorage(" + storage_id + "): ")
    url = "onepanel/provider/storages/" + storage_id
    response = request.delete(url)
    return response
