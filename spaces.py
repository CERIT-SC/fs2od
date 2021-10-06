import json
import sys
import time
import setting, request, tokens

def getSpaces():
    if setting.DEBUG >= 2: print("getSpaces(): ")
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/get_all_spaces
    url = "oneprovider/spaces"
    response = request.get(url)
    return response.json()

def removeSpace(space_id):
    if setting.DEBUG >= 2: print("removeSpace(" + space_id + "): ")
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/remove_space
    url = "onezone/spaces/" + space_id
    response = request.delete(url)
    return response

def getSpace(space_id):
    if setting.DEBUG >= 2: print("getSpace(" + space_id + "): ")
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/get_space
    url = "oneprovider/spaces/" + space_id
    response = request.get(url)
    return response.json()

def getSpaceDetails(space_id):    
    if setting.DEBUG >= 2: print("getSpaceDetails(" + space_id + "): ")
    # https://onedata.org/#/home/api/stable/onepanel?anchor=operation/get_space_details
    url = "onepanel/provider/spaces/" + space_id
    response = request.get(url)
    return response.json()

def getAutoStorageImportInfo(space_id):
    if setting.DEBUG >= 2: print("getAutoStorageImportInfo(" + space_id + "): ")
    # https://onedata.org/#/home/api/stable/onepanel?anchor=operation/get_auto_storage_import_info
    url = "onepanel/provider/spaces/" + space_id + "/storage-import/auto/info"
    response = request.get(url)
    return response.json()

def downloadFileContent(file_id):
    if setting.DEBUG >= 2: print("downloadFileContent(" + file_id + "): ")
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/download_file_content
    url = "oneprovider/data/" + file_id + "/content"
    response = request.get(url)
    return response

def listDirectory(file_id):
    if setting.DEBUG >= 2: print("listDirectory(" + file_id + "): ")
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/list_children
    url = "oneprovider/data/" + file_id + "/children"
    response = request.get(url)
    return response.json()

def createSpaceForGroup(group_id, space_name):
    if setting.TEST: space_name = setting.TEST_PREFIX + space_name
    if setting.DEBUG >= 2: print("createSpaceForGroup(" + group_id + ", " + space_name + "): ")
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/create_space_for_group
    url = "onezone/groups/" + group_id + "/spaces"
    my_data = {'name': space_name}
    headers = dict({'Content-type': 'application/json'})
    response = request.post(url, headers=headers, data=json.dumps(my_data))
    # Should return space ID in Headers
    location = response.headers["Location"]
    space_id = location.split("spaces/")[1]
    if space_id:
        if setting.DEBUG >= 1: print("Created space", space_name, "with id", space_id)
        return space_id
    else:
        if setting.DEBUG >= 0: print("Error: space cannot be created")

def supportSpace(token, size, storage_id):
    if setting.DEBUG >= 2: print("supportSpace(token, " + str(size) + ", " + storage_id + "): ")
    # https://onedata.org/#/home/api/stable/onepanel?anchor=operation/support_space
    url = "onepanel/provider/spaces"
    data = {
        'token': token["token"],
        'size': size,
        'storageId': storage_id,
        'storageImport': {
            'mode': 'auto',
            'autoStorageImportConfig': {
                'continuousScan': True,
                'scanInterval': setting.CONFIG['importingFiles']['scanInterval'],
            }
        }
    }
    
    headers = dict({'Content-type': 'application/json'})
    response = request.post(url, headers=headers, data=json.dumps(data))
    if response.ok:
        return response.json()["id"]
    else:
        if setting.DEBUG >= 0: print("Error: support cannot be set")

def setNewSizeToSpace(space_id, size):
    if setting.DEBUG >= 2: print("setNewSpaceSize(" + space_id + ", " + str(size) + "): ")
    # based on https://onedata.org/#/home/api/stable/onepanel?anchor=operation/modify_space
    url = "onepanel/provider/spaces/" + space_id
    data = {
        'size': size
    }
    headers = dict({'Content-type': 'application/json'})
    resp = request.patch(url, headers=headers, data=json.dumps(data))
    return resp

def createAndSupportSpaceForGroup(name, group_id, storage_id, capacity):
    space_id = createSpaceForGroup(group_id, name)
    token = tokens.createNamedTokenForUser(space_id, name, setting.CONFIG['serviceUserId'])
    time.sleep(3)
    supportSpace(token, capacity, storage_id)
    tokens.deleteNamedToken(token['tokenId'])
    return space_id

def setSizeOfSpaceByDataSize(space_id):
    if setting.DEBUG: print("setSizeOfSpaceByDataSize(" + space_id + "): ")
    sd = getSpaceDetails(space_id)
    if sd['importedStorage'] == True and getAutoStorageImportInfo(space_id)['status'] == "completed":
        new_size = sd['spaceOccupancy']
        setNewSizeToSpace(space_id, new_size)
        if setting.DEBUG >= 1: print("Set up new size", new_size, "for space", space_id)

def enableContinuousImport(space_id):
    if not getContinuousImportStatus(space_id):
        setContinuousImport(space_id, True)

def disableContinuousImport(space_id):
    if getContinuousImportStatus(space_id):
        setContinuousImport(space_id, False)

def getContinuousImportStatus(space_id):
    space_details = getSpaceDetails(space_id)
    if space_details['importedStorage']:
        return space_details['storageImport']['autoStorageImportConfig']['continuousScan']
    else:
        if setting.DEBUG >= 1: print("Warning: Value not available, space is not imported.")
        return None

def setContinuousImport(space_id, newValue):
    if setting.DEBUG >= 2: print("setContinuousImport(" + space_id + ", " + str(newValue) + "): ")
    # https://onedata.org/#/home/api/21.02.0-alpha21/onepanel?anchor=operation/modify_space
    url = "onepanel/provider/spaces/" + space_id
    data = {
        'autoStorageImportConfig': {
            'continuousScan': newValue,
            'scanInterval': setting.CONFIG['importingFiles']['scanInterval'],
        }
    }
    headers = dict({'Content-type': 'application/json'})
    resp = request.patch(url, headers=headers, data=json.dumps(data))

def listSpaceGroups(space_id):
    if setting.DEBUG >= 2: print("listSpacegroups(" + space_id + "): ")
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/list_space_groups
    url = "onezone/spaces/"+ space_id + "/groups"
    response = request.get(url)
    return response.json()['groups']
