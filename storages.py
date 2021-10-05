import json
import requests
from setting import *


def getStorages():
    if DEBUG >= 2: print("getStorages(): ")
    # https://onedata.org/#/home/api/stable/onepanel?anchor=operation/get_storages
    url = ONEPANEL_API_URL + "onepanel/provider/storages"
    response = requests.get(url, headers=ONEPANEL_AUTH_HEADERS, verify=False)
    if DEBUG >= 3: pprint(response)
    return response.json()

def getLastStorage():
    if DEBUG >= 2: print("getLastStorage(): ")
    storages = getStorages()
    if DEBUG >= 3: print(storages['ids'][0:1])
    return storages['ids'][0]

def addStorage(name, mountpoint):
    if DEBUG >= 2: print("addStorage(" + name + ", " + mountpoint + "): ")
    url = ONEPANEL_API_URL + "onepanel/provider/storages"
    data = {
        name: {
            "type": "posix",
            "importedStorage": True,
            "readonly": True,
            "mountPoint": mountpoint
        }
    }
    headers = dict(ONEPANEL_AUTH_HEADERS)
    headers['Content-type'] = 'application/json'
    resp = requests.post(url, headers=headers, data=json.dumps(data), verify=False)
    if DEBUG >= 3: print(resp)
    return resp

def getStorageDetails(id):
    if DEBUG >= 2: print("getStorageDetails(" + id + "): ")
    url = ONEPANEL_API_URL + "onepanel/provider/storages/" + id
    response = requests.get(url, headers=ONEPANEL_AUTH_HEADERS, verify=False)
    if DEBUG >= 3: pprint(response)
    return response.json()

def createAndGetStorage(name, mountpoint):
    if TEST: name = TEST_PREFIX + name
    resp = addStorage(name, mountpoint)
    if resp.status_code == 204:
        last_id = getLastStorage()
        # porovnat zda se rovnaji jmena
        if getStorageDetails(last_id)['name'] == name:
            if DEBUG >= 1: print("Storage", name, "created with id", last_id)
            return last_id
        else:
            print("Warning: storage added but id cannot be returned")
    else:
        print("Error: failed while adding storage, response is ", resp)

def removeStorage(id):
    if DEBUG >= 2: print("removeStorage(" + id + "): ")
    url = ONEPANEL_API_URL + "onepanel/provider/storages/" + id
    response = requests.delete(url, headers=ONEPANEL_AUTH_HEADERS, verify=False)
    if DEBUG >= 3: pprint(response)
    return response
