import json
import time
from settings import Settings
from  utils import Logger, Utils
import request, tokens, files, metadata

"""
Minimal size of a space. Smaller size cause "badValueTooLow" error on Oneprovder. 
1 MB = 1*2**20 = 1048576
"""
MINIMAL_SPACE_SIZE = 1048576

def getSpaces():
    Logger.log(4, "getSpaces():")
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/get_all_spaces
    url = "oneprovider/spaces"
    response = request.get(url)
    return response.json()

def removeSpace(space_id):
    Logger.log(4, "removeSpace(%s):" % space_id)
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/remove_space
    url = "onezone/spaces/" + space_id
    response = request.delete(url)
    return response

def getSpace(space_id):
    Logger.log(4, "getSpace(%s):" % space_id)
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/get_space
    url = "oneprovider/spaces/" + space_id
    response = request.get(url)
    return response.json()

def getSpaceDetails(space_id):
    Logger.log(4, "getSpaceDetails(%s):" % space_id)
    # https://onedata.org/#/home/api/stable/onepanel?anchor=operation/get_space_details
    url = "onepanel/provider/spaces/" + space_id
    response = request.get(url)
    return response.json()

def getAutoStorageImportInfo(space_id):
    Logger.log(4, "getAutoStorageImportInfo(%s):" % space_id)
    # https://onedata.org/#/home/api/stable/onepanel?anchor=operation/get_auto_storage_import_info
    url = "onepanel/provider/spaces/" + space_id + "/storage-import/auto/info"
    response = request.get(url)
    return response.json()

def startAutoStorageImport(space_id):
    Logger.log(4, "startAutoStorageImport(%s):" % space_id)
    # https://onedata.org/#/home/api/stable/onepanel?anchor=operation/force_start_auto_storage_import_scan
    url = "onepanel/provider/spaces/" + space_id + "/storage-import/auto/force-start"
    response = request.post(url)
    return response

def stopAutoStorageImport(space_id):
    Logger.log(4, "stopAutoStorageImport(%s):" % space_id)
    # https://onedata.org/#/home/api/stable/onepanel?anchor=operation/force_start_auto_storage_import_scan
    url = "onepanel/provider/spaces/" + space_id + "/storage-import/auto/force-stop"
    response = request.post(url)
    return response

def createSpaceForGroup(group_id, space_name):
    if Settings.get().TEST: space_name = Settings.get().TEST_PREFIX + space_name
    Logger.log(4, "createSpaceForGroup(%s, %s):" % (group_id, space_name))
    
    if len(space_name) < Settings.get().MIN_ONEDATA_NAME_LENGTH:
        Logger.log(1, "Too short space name %s." % space_name)
        return

    space_name = Utils.clearOnedataName(space_name)

    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/create_space_for_group
    url = "onezone/groups/" + group_id + "/spaces"
    my_data = {'name': space_name}
    headers = dict({'Content-type': 'application/json'})
    response = request.post(url, headers=headers, data=json.dumps(my_data))
    # Should return space ID in Headers
    location = response.headers["Location"]
    space_id = location.split("spaces/")[1]
    if space_id:
        Logger.log(3, "Space %s was created with space ID %s" % (space_name, space_id))
        return space_id
    else:
        Logger.log(1, "Space %s can't be created" % space_name)

def supportSpace(token, size, storage_id):
    Logger.log(4, "supportSpace(token, %s, %s)" % (size, storage_id))
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
        Logger.log(1, "Space support can't' be set on starage ID %s" % storage_id)

def setSpaceSize(space_id, size = None):
    """
    Set a new given size to space with given space_id. 
    If size is not set, it set up a new size of space to be equal to actuall space occupancy. 
    """
    Logger.log(4, "setSpaceSize(%s, %s):" % (space_id, str(size)))
    # if size not set, get spaceOccupancy
    if not size:
        sd = getSpaceDetails(space_id)
        size = sd['spaceOccupancy']

    # fix space size if it is too small
    if size < MINIMAL_SPACE_SIZE:
        Logger.log(3, "Space size fixed (%s -> %s)" % (size, MINIMAL_SPACE_SIZE))
        size = MINIMAL_SPACE_SIZE

    # based on https://onedata.org/#/home/api/stable/onepanel?anchor=operation/modify_space
    url = "onepanel/provider/spaces/" + space_id
    data = {
        'size': size
    }
    headers = dict({'Content-type': 'application/json'})
    response = request.patch(url, headers=headers, data=json.dumps(data))
    if response.ok:
        Logger.log(3, "New size (%s) set for space %s" % (size, space_id))
    else:
        Logger.log(2, "New size (%s) can't be set for space %s" % (size, space_id))
    return response

def createAndSupportSpaceForGroup(name, group_id, storage_id, capacity):
    Logger.log(4, "createAndSupportSpaceForGroup(%s, group_id, storage_id, capacity):" % name)
    space_id = createSpaceForGroup(group_id, name)
    token = tokens.createNamedTokenForUser(space_id, name, Settings.get().config['serviceUserId'])
    time.sleep(3 * Settings.get().config['sleepFactor'])
    supportSpace(token, capacity, storage_id)
    tokens.deleteNamedToken(token['tokenId'])
    return space_id

def enableContinuousImport(space_id):
    Logger.log(4, "enableContinuousImport(%s):" % space_id)
    # running file exists, permissions should be periodically set to new dirs and files have given permissions
    file_id = getSpace(space_id)['fileId']
    files.setFileAttributeRecursive(file_id, Settings.get().config['initialPOSIXlikePermissions'])

    if not getContinuousImportStatus(space_id):
        setSpaceSize(space_id, Settings.get().config['implicitSpaceSize'])
        time.sleep(1 * Settings.get().config['sleepFactor'])
        result = setContinuousImport(space_id, True)
        if result:
            Logger.log(3, "Continuous import enabled for space with ID %s" % space_id)
            # continous import is enabled now
            # force (full) import of files immediately
            startAutoStorageImport(space_id)

def disableContinuousImport(space_id):
    Logger.log(4, "disableContinuousImport(%s):" % space_id)
    if getContinuousImportStatus(space_id):
        result = setContinuousImport(space_id, False)
        if result:
            Logger.log(3, "Continuous import disabled for space with ID %s" % space_id)
            time.sleep(1 * Settings.get().config['sleepFactor'])
            # continous import is disabled now
            # force (full) import of files last time
            startAutoStorageImport(space_id)

            # permissions of all dirs and file should set to given permissions
            file_id = getSpace(space_id)['fileId']
            files.setFileAttributeRecursive(file_id, Settings.get().config['initialPOSIXlikePermissions'])

            # Set metadata for the space
            if Settings.get().config['importMetadata']:
                metadata.setSpaceMetadataFromYaml(space_id)

            # set the space size to space occupancy
            setSpaceSize(space_id)

def getContinuousImportStatus(space_id):
    Logger.log(4, "getContinuousImportStatus(%s):" % space_id)
    space_details = getSpaceDetails(space_id)
    if space_details['importedStorage']:
        return space_details['storageImport']['autoStorageImportConfig']['continuousScan']
    else:
        Logger.log(2, "Imported storage value not available, space %s isn't imported" % space_id)
        return None

def setContinuousImport(space_id, continuousScanEnabled):
    Logger.log(4, "setContinuousImport(%s, %s):" % (space_id, str(continuousScanEnabled)))
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
        Logger.log(2, "Continuous scan can't be changed for the space %s" % space_id)
        if autoStorageImportInfo != "completed":
            Logger.log(2, "Import of files is not completed yet")
        return False

def listSpaceGroups(space_id):
    Logger.log(4, "listSpaceGroups(%s):" % space_id)
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/list_space_groups
    url = "onezone/spaces/"+ space_id + "/groups"
    response = request.get(url)
    return response.json()['groups']

def addGroupToSpace(space_id, gid, privileges = None):
    """
    Add given group to the space. The third argument is list of the privileges, 
    which the group will be given on the space. 
    If no privileges are given, default privileges are used.
    """
    Logger.log(4, "addGroupToSpace(%s, %s, %s):" % (space_id, gid, privileges))
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/add_group_to_space
    url = "onezone/spaces/" + space_id + "/groups/" + gid
    headers = dict({'Content-type': 'application/json'})
    data = {
        "privileges": privileges
    }
    response = request.put(url, headers=headers, data=json.dumps(data))
    if response.ok:
        Logger.log(3, "Space %s was added as member of group %s" % (space_id, gid))
        return response
    else:
        Logger.log(1, "Space %s wasn't added as member of group %s" % (space_id, gid))
        return response
