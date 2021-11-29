import json
import sys
import time
from settings import Settings
import request, tokens, files, metadata

def getSpaces():
    if Settings.get().debug >= 2: print("getSpaces(): ")
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/get_all_spaces
    url = "oneprovider/spaces"
    response = request.get(url)
    return response.json()

def removeSpace(space_id):
    if Settings.get().debug >= 2: print("removeSpace(" + space_id + "): ")
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/remove_space
    url = "onezone/spaces/" + space_id
    response = request.delete(url)
    return response

def getSpace(space_id):
    if Settings.get().debug >= 2: print("getSpace(" + space_id + "): ")
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/get_space
    url = "oneprovider/spaces/" + space_id
    response = request.get(url)
    return response.json()

def getSpaceDetails(space_id):    
    if Settings.get().debug >= 2: print("getSpaceDetails(" + space_id + "): ")
    # https://onedata.org/#/home/api/stable/onepanel?anchor=operation/get_space_details
    url = "onepanel/provider/spaces/" + space_id
    response = request.get(url)
    return response.json()

def getAutoStorageImportInfo(space_id):
    if Settings.get().debug >= 2: print("getAutoStorageImportInfo(" + space_id + "): ")
    # https://onedata.org/#/home/api/stable/onepanel?anchor=operation/get_auto_storage_import_info
    url = "onepanel/provider/spaces/" + space_id + "/storage-import/auto/info"
    response = request.get(url)
    return response.json()

def createSpaceForGroup(group_id, space_name):
    if Settings.get().TEST: space_name = Settings.get().TEST_PREFIX + space_name
    if Settings.get().debug >= 2: print("createSpaceForGroup(" + group_id + ", " + space_name + "): ")
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/create_space_for_group
    url = "onezone/groups/" + group_id + "/spaces"
    my_data = {'name': space_name}
    headers = dict({'Content-type': 'application/json'})
    response = request.post(url, headers=headers, data=json.dumps(my_data))
    # Should return space ID in Headers
    location = response.headers["Location"]
    space_id = location.split("spaces/")[1]
    if space_id:
        if Settings.get().debug >= 1: print("Space", space_name, "was created with id", space_id)
        return space_id
    else:
        if Settings.get().debug >= 0: print("Error: space cannot be created")

def supportSpace(token, size, storage_id):
    if Settings.get().debug >= 2: print("supportSpace(token, " + str(size) + ", " + storage_id + "): ")
    # https://onedata.org/#/home/api/stable/onepanel?anchor=operation/support_space
    url = "onepanel/provider/spaces"
    data = {
        'token': token["token"],
        'size': size,
        'storageId': storage_id,
        'storageImport': {
            'mode': 'auto',
            'autoStorageImportConfig': {
                'continuousScan': Settings.get().config['continousFileImport']['enabled'],
                'scanInterval': Settings.get().config['continousFileImport']['scanInterval'],
                'detectModifications': Settings.get().config['continousFileImport']['detectModifications'],
                'detectDeletions': Settings.get().config['continousFileImport']['detectDeletions'],
            }
        }
    }
    
    headers = dict({'Content-type': 'application/json'})
    response = request.post(url, headers=headers, data=json.dumps(data))
    if response.ok:
        return response.json()["id"]
    else:
        if Settings.get().debug >= 0: print("Error: support cannot be set")

def setSpaceSize(space_id, size = None):
    """
    Set a new given size to space with given space_id. 
    If size is not set, it set up a new size of space to be equal to actuall space occupancy. 
    """
    if Settings.get().debug >= 2: print("setSpaceSize(" + space_id + ", " + str(size) + "): ")
    # if size not set, get spaceOccupancy
    if not size:
        sd = getSpaceDetails(space_id)
        size = sd['spaceOccupancy']

    # based on https://onedata.org/#/home/api/stable/onepanel?anchor=operation/modify_space
    url = "onepanel/provider/spaces/" + space_id
    data = {
        'size': size
    }
    headers = dict({'Content-type': 'application/json'})
    response = request.patch(url, headers=headers, data=json.dumps(data))
    if response.ok:
        if Settings.get().debug >= 1: print("Sew size (", size, ") set for space with id", space_id)
    else:
        if Settings.get().debug >= 1: print("New size (", size, ") can't be set for space with id", space_id)
    return response

def createAndSupportSpaceForGroup(name, group_id, storage_id, capacity):
    space_id = createSpaceForGroup(group_id, name)
    token = tokens.createNamedTokenForUser(space_id, name, Settings.get().config['serviceUserId'])
    time.sleep(3)
    supportSpace(token, capacity, storage_id)
    tokens.deleteNamedToken(token['tokenId'])
    return space_id

def enableContinuousImport(space_id):
    # running file exists, permissions should be periodically set to new dirs and files have given permissions
    file_id = getSpace(space_id)['fileId']
    files.setFileAttributeRecursive(file_id, Settings.get().config['initialPOSIXlikePermissions'])

    if not getContinuousImportStatus(space_id):
        setSpaceSize(space_id, Settings.get().config['implicitSpaceSize'])
        time.sleep(1)
        result = setContinuousImport(space_id, True)
        if result:
            if Settings.get().debug >= 1: print("Continuous import enabled for space with id", space_id)

def disableContinuousImport(space_id):
    if getContinuousImportStatus(space_id):
        result = setContinuousImport(space_id, False)
        if result:
            if Settings.get().debug >= 1: print("Continuous import disabled for space with id", space_id)
            time.sleep(1)
            # continous import is disabling now, permissions of all dirs and file should set to given permissions
            file_id = getSpace(space_id)['fileId']
            files.setFileAttributeRecursive(file_id, Settings.get().config['initialPOSIXlikePermissions'])
            # Set metadata for the space
            metadata.setSpaceMetadataFromYaml(space_id)
            # set the space size to space occupancy
            setSpaceSize(space_id)

def getContinuousImportStatus(space_id):
    space_details = getSpaceDetails(space_id)
    if space_details['importedStorage']:
        return space_details['storageImport']['autoStorageImportConfig']['continuousScan']
    else:
        if Settings.get().debug >= 1: print("Warning: Value not available, space is not imported.")
        return None

def setContinuousImport(space_id, continuousScanEnabled):
    if Settings.get().debug >= 2: print("setContinuousImport(" + space_id + ", " + str(continuousScanEnabled) + "): ")
    autoStorageImportInfo = getAutoStorageImportInfo(space_id)['status']
    # test if import was completed
    if Settings.get().config['continousFileImport']['enabled'] and autoStorageImportInfo == "completed":
        # https://onedata.org/#/home/api/21.02.0-alpha21/onepanel?anchor=operation/modify_space
        url = "onepanel/provider/spaces/" + space_id
        data = {
            'autoStorageImportConfig': {
                'continuousScan': continuousScanEnabled,
                'scanInterval': Settings.get().config['continousFileImport']['scanInterval'],
                'detectModifications': Settings.get().config['continousFileImport']['detectModifications'],
                'detectDeletions': Settings.get().config['continousFileImport']['detectDeletions'],
            }
        }
        headers = dict({'Content-type': 'application/json'})
        response = request.patch(url, headers=headers, data=json.dumps(data))
        if response.ok:
            return True
    else:
        if Settings.get().debug >= 1: print("Warning: Continuous scan can't be changed for the space with id", space_id)
        if autoStorageImportInfo != "completed":
            if Settings.get().debug >= 1: print("Import of files is not completed yet")
        return False

def listSpaceGroups(space_id):
    if Settings.get().debug >= 2: print("listSpacegroups(" + space_id + "): ")
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/list_space_groups
    url = "onezone/spaces/"+ space_id + "/groups"
    response = request.get(url)
    return response.json()['groups']
