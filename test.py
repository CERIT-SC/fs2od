from pprint import pprint
import time
import spaces, storages, groups, tokens

def deleteAllTestInstances(prefix):
    """
    Delete all instances of a given prefix.
    Should by called from cmd by:
    python -c 'from test import deleteAllTestInstances; deleteAllTestInstances("some_prefix")'
    """
    # safety notice
    if False:
        print("Dangerous method! You should edit line above to run deleteAllTestInstances(" + prefix + ")")
        return

    # invite tokens
    deleted_tokens = 0
    for tokenId in tokens.listAllNamedtokens():
        token = tokens.getNamedToken(tokenId)
        if token['name'].startswith(prefix):
            tokens.deleteNamedToken(tokenId)
            print("Token", token['name'], "deleted. ")
            deleted_tokens += 1
            time.sleep(0.5)

    # spaces
    deleted_spaces = 0
    for space in spaces.getSpaces():
        if space['name'].startswith(prefix):
            spaces.removeSpace(space['spaceId'])
            print("Space", space['name'], "deleted. ")
            deleted_spaces += 1
            time.sleep(0.5)
    
    # groups
    deleted_groups = 0
    # TODO - there is no getGroups()
    # for group in groups.getGroups():
    #     pprint(group)
    #     if group['name'].startwith(prefix):
    #         groups.removeGroup(group_id)
    #         print("Group", group['name'], "deleted. ")
    #         deleted_groups += 1
    #         time.sleep(0.5)

    # storages
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
