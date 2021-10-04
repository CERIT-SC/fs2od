import json
import sys
import time
from setting import *
import tokens

def getSpaces():
    if DEBUG: print("getSpaces(): ")
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/get_all_spaces
    url = ONEPROVIDER_API_URL + "oneprovider/spaces"
    response = requests.get(url, headers=ONEZONE_AUTH_HEADERS, verify=False)
    if DEBUG: print(response)
    if DEBUG: pprint(response.json())
    return response.json()

def removeSpace(space_id):
    if DEBUG: print("removeSpace(" + space_id + "): ")
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/remove_space
    url = ONEZONE_API_URL + "onezone/spaces/" + space_id
    response = requests.delete(url, headers=ONEZONE_AUTH_HEADERS, verify=False)
    if DEBUG: print(response)
    return response

def getSpace(space_id):
    if DEBUG: print("getSpace(" + space_id + "): ")
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/get_space
    url = ONEPROVIDER_API_URL + "oneprovider/spaces/" + space_id
    timeout = 3
    while timeout > 0:
        response = requests.get(url, headers=ONEZONE_AUTH_HEADERS, verify=False)
        if response.ok:
            timeout = 0
        else:
            if DEBUG: print("Timeouted", str(4-timeout), "ouf of 3 times;" )
            timeout = timeout - 1
            time.sleep(5)
    if DEBUG: pprint(response.json())
    return response.json()

def getSpaceDetails(space_id):    
    if DEBUG: print("getSpaceDetails(" + space_id + "): ")
    # https://onedata.org/#/home/api/stable/onepanel?anchor=operation/get_space_details
    url = ONEPROVIDER_API_URL + "onepanel/provider/spaces/" + space_id
    response = requests.get(url, headers=ONEPANEL_AUTH_HEADERS, verify=False)
    if DEBUG: pprint(response.json())
    return response.json()

def getAutoStorageImportInfo(space_id):
    if DEBUG: print("getAutoStorageImportInfo(" + space_id + "): ")
    # https://onedata.org/#/home/api/stable/onepanel?anchor=operation/get_auto_storage_import_info
    url = ONEPROVIDER_API_URL + "onepanel/provider/spaces/" + space_id + "/storage-import/auto/info"
    response = requests.get(url, headers=ONEPANEL_AUTH_HEADERS, verify=False)
    if DEBUG: pprint(response.json())
    return response.json()

def downloadFileContent(file_id):
    if DEBUG: print("downloadFileContent(" + file_id + "): ")
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/download_file_content
    url = ONEPROVIDER_API_URL + "oneprovider/data/" + file_id + "/content"
    response = requests.get(url, headers=ONEZONE_AUTH_HEADERS, verify=False)
    if DEBUG: pprint(response)
    return response

def listDirectory(file_id):
    if DEBUG: print("listDirectory(" + file_id + "): ")
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/list_children
    url = ONEPROVIDER_API_URL + "oneprovider/data/" + file_id + "/children"
    response = requests.get(url, headers=ONEZONE_AUTH_HEADERS, verify=False)
    if DEBUG: pprint(response.json())
    return response.json()

def createSpaceForGroup(group_id, space_name):
    if DEBUG: print("createSpaceForGroup(" + group_id + ", " + space_name + "): ")
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/create_space_for_group
    url = ONEZONE_API_URL + "onezone/groups/" + group_id + "/spaces"
    my_data = {'name': space_name}
    headers = dict(ONEZONE_AUTH_HEADERS)
    headers['Content-type'] = 'application/json'
    resp = requests.post(url, headers=headers, data=json.dumps(my_data), verify=False)
    # Should return space ID in Headers
    location = resp.headers["Location"]
    space_id = location.split("spaces/")[1]
    if DEBUG: print(space_id)
    return space_id

def supportSpace(token, size, storage_id):
    if DEBUG: print("supportSpace(" + token + ", " + str(size) + ", " + storage_id + "): ")
    # https://onedata.org/#/home/api/stable/onepanel?anchor=operation/support_space
    url = ONEPANEL_API_URL + "onepanel/provider/spaces"
    data = {
        'token': token["token"],
        'size': size,
        'storageId': storage_id,
        'storageImport': {
            'mode': 'auto',
            'autoStorageImportConfig': {
                'continuousScan': False,
            }
        }
    }
    my_headers = dict(ONEPANEL_AUTH_HEADERS)
    my_headers['Content-type'] = 'application/json'
    resp = requests.post(url, headers=my_headers, data=json.dumps(data), verify=False)
    #return resp.json()["id"]

def setNewSizeToSpace(space_id, size):
    if DEBUG: print("setNewSpaceSize(" + space_id + ", " + str(size) + "): ")
    # based on https://onedata.org/#/home/api/stable/onepanel?anchor=operation/modify_space
    url = ONEPANEL_API_URL + "onepanel/provider/spaces/" + space_id
    data = {
        'size': size
    }
    my_headers = dict(ONEPANEL_AUTH_HEADERS)
    my_headers['Content-type'] = 'application/json'
    resp = requests.patch(url, headers=my_headers, data=json.dumps(data), verify=False)
    return resp

def createAndSupportSpaceForGroup(name, group_id, storage_id, capacity):
    space_id = createSpaceForGroup(group_id, name)
    token = tokens.createNamedTokenForUser(space_id, name, CONFIG['serviceUserId'])
    time.sleep(1)
    supportSpace(token, capacity, storage_id)
    tokens.deleteNamedToken(token['tokenId'])
    return space_id

def setSizeOfSpaceByDataSize(space_id):
    if DEBUG: print("setSizeOfSpaceByDataSize(" + space_id + "): ")
    sd = getSpaceDetails(space_id)
    if sd['importedStorage'] == True and getAutoStorageImportInfo(space_id)['status'] == "completed":
        new_size = sd['spaceOccupancy']
        setNewSizeToSpace(space_id, new_size)
        if DEBUG: print("Set up new size", new_size, "for space", space_id)

def enableContinuousImport(space_id):
    if not getContinuousImportStatus(space_id):
        setContinuousImport(space_id, True)

def disableContinuousImport(space_id):
    if getContinuousImportStatus(space_id):
        setContinuousImport(space_id, False)

def getContinuousImportStatus(space_id):
    space_details = getSpaceDetails(space_id)
    if space_details['importedStorage']:
        space_import_info = getAutoStorageImportInfo(space_id)
        if DEBUG: pprint(space_import_info)
        return space_import_info['storageImport']['autoStorageImportConfig']['continuousScan']
    else:
        print("Space is not imported.")
        return None

def setContinuousImport(space_id, newValue):
    if DEBUG: print("setContinuousImport(" + space_id + ", " + str(newValue) + "): ")
    # https://onedata.org/#/home/api/21.02.0-alpha21/onepanel?anchor=operation/modify_space
    url = ONEPANEL_API_URL + "onepanel/provider/spaces/" + space_id
    data = {
        'autoStorageImportConfig': {
            'continuousScan': newValue,
            'scanInterval': CONFIG['importingFiles']['scanInterval'],
            }
    }
    my_headers = dict(ONEPANEL_AUTH_HEADERS)
    my_headers['Content-type'] = 'application/json'
    resp = requests.patch(url, headers=my_headers, data=json.dumps(data), verify=False)
