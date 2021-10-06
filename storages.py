from pprint import pprint
import json
import setting, request

def getStorages():
    if setting.DEBUG >= 2: print("getStorages(): ")
    # https://onedata.org/#/home/api/stable/onepanel?anchor=operation/get_storages
    url = "onepanel/provider/storages"
    response = request.get(url)
    return response.json()

def getLastStorage():
    if setting.DEBUG >= 2: print("getLastStorage(): ")
    storages = getStorages()
    if setting.DEBUG >= 3: print(storages['ids'][0:1])
    return storages['ids'][0]

def addStorage(name, mountpoint):
    if setting.DEBUG >= 2: print("addStorage(" + name + ", " + mountpoint + "): ")
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
    if setting.DEBUG >= 2: print("getStorageDetails(" + id + "): ")
    url = "onepanel/provider/storages/" + id
    response = request.get(url)
    return response.json()

def createAndGetStorage(name, mountpoint):
    if setting.TEST: name = setting.TEST_PREFIX + name
    resp = addStorage(name, mountpoint)
    if resp.status_code == 204:
        last_id = getLastStorage()
        # porovnat zda se rovnaji jmena
        if getStorageDetails(last_id)['name'] == name:
            if setting.DEBUG >= 1: print("Storage", name, "created with id", last_id)
            return last_id
        else:
            print("Warning: storage added but id cannot be returned")
    else:
        print("Error: failed while adding storage, response is ", resp)

def removeStorage(storage_id):
    if setting.DEBUG >= 2: print("removeStorage(" + storage_id + "): ")
    url = "onepanel/provider/storages/" + storage_id
    response = request.delete(url)
    return response
