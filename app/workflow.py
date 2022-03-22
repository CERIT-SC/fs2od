import json
import sys
import time
from pprint import pprint
from settings import Settings
import spaces, tokens, groups, storages

# TODO - WIP
def deleteSpaceWithAllStuff(spaceId):
    res_spaces = spaces.getSpaces()
    for s in res_spaces:
        if spaceId == s['spaceId']:
            space_name = s['name']
    
    if space_name == "211226_70SRNAP_A1":
        return
    
    # invite tokens
    deleted_tokens = 0
    for tokenId in tokens.listAllNamedtokens():
        token = tokens.getNamedToken(tokenId)
        if space_name in token['name']:
            tokens.deleteNamedToken(tokenId)
            print("*** Token", token['name'], "deleted. ")
            deleted_tokens += 1
            time.sleep(0.5)
    
    # spaces and groups associated to given spaces
    deleted_spaces = 0
    deleted_groups = 0
    for space in spaces.getSpaces():
        if space_name in space['name']:

            # remove group 
            space_groups = spaces.listSpaceGroups(space['spaceId'])
            for groupId in space_groups:
                pprint(groups.getGroupDetails(groupId))
                group_name = groups.getGroupDetails(groupId)['name']
                if space_name in group_name:
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
        if space_name in storage['name']:
            storages.removeStorage(storageId)
            print("Storage", storage['name'], "deleted. ")
            deleted_storages += 1
            time.sleep(0.5)
