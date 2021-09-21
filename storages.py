import json
from setting import *

def getStorages():
    if DEBUG: print("Getting storages: ")
    # https://onedata.org/#/home/api/stable/onepanel?anchor=operation/get_storages
    url = ONEPANEL_API_URL + "onepanel/provider/storages"
    response = requests.get(url, headers=ONEPANEL_AUTH_HEADERS, verify=False)

    if DEBUG: pprint(response.json())
    return response.json()

def getLastStorage():
    if DEBUG: print("Getting last storage: ")
    storages = getStorages()
    if DEBUG: print(storages['ids'][0:1])
    return storages['ids'][0]

def addStorage(name, mountpoint):
    if DEBUG: print("Adding storage: ")
    url = ONEPANEL_API_URL + "onepanel/provider/storages"
    data = {
        name: {
            "type": "posix",
            "importedStorage": True,
            "readonly": True,
            "mountPoint": mountpoint
        }
    }
    
    if DEBUG: pprint(data)
    headers = dict(ONEPANEL_AUTH_HEADERS)
    headers['Content-type'] = 'application/json'
    resp = requests.post(url, headers=headers, data=json.dumps(data), verify=False)
    if DEBUG: print(resp)
    return resp

def getStorageDetails(id):
    if DEBUG: print("getStorageDetails(" + id + "): ")
    url = ONEPANEL_API_URL + "onepanel/provider/storages/" + id
    response = requests.get(url, headers=ONEPANEL_AUTH_HEADERS, verify=False)
    if DEBUG: pprint(response)
    return response.json()

def createAndGetStorage(name, mountpoint):
    resp = addStorage(name, mountpoint)
    if resp.status_code == 204:
        last_id = getLastStorage()
        # porovnat zda se rovnaji jmena
        if getStorageDetails(last_id)['name'] == name:
            if DEBUG: print("return id", last_id)
            return last_id
        else:
            print("Warning: storage added but id cannot be returned")
    else:
        print("Error: failed while adding storage, response is ", resp)

def removeStorage(id):
    if DEBUG: print("Removing storage: ")
    url = ONEPANEL_API_URL + "onepanel/provider/storages/" + id
    response = requests.delete(url, headers=ONEPANEL_AUTH_HEADERS, verify=False)
    if DEBUG: pprint(response)
    return response
