from pprint import pprint
import time
import argparse
import spaces, storages, groups, tokens

def deleteAllTestInstances(prefix):
    """
    Delete all instances of a given prefix.
    Should by called from cmd by:
    python3 test.py --remove_instances some_prefix
    """
    # safety notice
    print("Possibly dangerous action!")
    if input("If you yould like continue, write 'yes': ") != "yes":
        print("Exiting.")
        return

    print("Deleting all spaces, groups, tokens and storages with the prefix \"" + prefix + "\".")

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
