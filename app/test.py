from pprint import pprint
import time
import sys
from settings import Settings
from utils import Logger
import spaces, storages, groups, request, tokens

def safetyNotice(message):
    print("*** Possibly dangerous action! ***")
    print(message)
    if input("If you yould like continue, write 'yes': ") != "yes":
        print("Exiting.")
        sys.exit(1)

def deleteAllTestInstances(prefix):
    """
    Delete all instances of a given prefix.
    """
    if not prefix:
        prefix = Settings.get().TEST_PREFIX

    safetyNotice("All spaces, groups, tokens and storages with the prefix \"" + prefix + "\" will be deleted.")

    # invite tokens
    deleted_tokens = 0
    for tokenId in tokens.listAllNamedtokens():
        token = tokens.getNamedToken(tokenId)
        if token['name'].startswith(prefix):
            tokens.deleteNamedToken(tokenId)
            print("Token", token['name'], "deleted. ")
            deleted_tokens += 1
            time.sleep(0.5)

    # spaces and groups associated to given spaces
    deleted_spaces = 0
    deleted_groups = 0
    for space in spaces.getSpaces():
        if space['name'].startswith(prefix):

            # remove group 
            space_groups = spaces.listSpaceGroups(space['spaceId'])
            for groupId in space_groups:
                group_name = groups.getGroupDetails(groupId)['name']
                if group_name.startswith(prefix):
                    groups.removeGroup(groupId)
                    print("Group", group_name, "deleted. ")
                    deleted_groups += 1
                    time.sleep(0.5)

            spaces.removeSpace(space['spaceId'])
            print("Space", space['name'], "deleted. ")
            deleted_spaces += 1
            time.sleep(0.5)

    # storages
    time.sleep(3) # Removing of spaces have to be propagated to Oneprovider
    deleted_storages = 0
    for storageId in storages.getStorages()['ids']:
        storage = storages.getStorageDetails(storageId)
        if storage['name'].startswith(prefix):
            storages.removeStorage(storageId)
            print("Storage", storage['name'], "deleted. ")
            deleted_storages += 1
            time.sleep(0.5)

    print("Spaces deleted =", deleted_spaces)
    print("Tokens deleted =", deleted_tokens)
    print("Groups deleted =", deleted_groups)
    print("Storages deleted =", deleted_storages)

def deleteAllTestGroups(prefix):
    """
    Delete all groups of a given prefix.
    """
    if not prefix:
        prefix = Settings.get().TEST_PREFIX

    safetyNotice("All groups with the prefix \"" + prefix + "\" will be deleted.")
    
    deleted_groups = 0 
    user_groups = groups.listEffectiveUserGroups()
    for groupId in user_groups:
        group_name = groups.getGroupDetails(groupId)['name']
        if group_name.startswith(prefix):
            groups.removeGroup(groupId)
            print("Group", group_name, "deleted. ")
            deleted_groups += 1
            time.sleep(0.5)

    print("Groups deleted =", deleted_groups)

def _testOnezone():
    Logger.log(4, "_testOnezone():")
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/get_configuration
    url = "onezone/configuration"
    response = request.get(url)
    # test if a attribute exists
    if "build" in response.json(): 
        return 0
    else:
        return 1

def _testOneprovider():
    Logger.log(4, "_testOneprovider():")
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/get_configuration
    url = "oneprovider/configuration"
    response = request.get(url)
    # test if a attribute exists
    if "build" in response.json(): 
        return 0
    else:
        return 2

def testConnection():
    result = _testOnezone()
    result = result + _testOneprovider()
    
    if result == 0:
        Logger.log(3, "Onezone and Oneprovider exist.")
    elif result == 1:
        Logger.log(1, "Onezone doesn't exist.")
    elif result == 2:
        Logger.log(1, "Oneprovider doesn't exist.")
    elif result == 3:
        Logger.log(1, "Onezone and Oneprovider don't exist.")
    return result

def registerSpace(path):
    Logger.log(1, "Not fully implemeted yet")
    sys.exit(1)

    # if last char is os.sep(/) remove it
    if path[-1] == os.sep:
        path = path[0:len(path)-1]

    # split according to last os.sep char (/)
    temp = path.rsplit(os.sep, 1)
    base_path = temp[0]
    directory = temp[1]

    workflow.registerSpace(base_path, directory)
