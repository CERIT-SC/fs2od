import os
import time
import sys
from pprint import pprint
from settings import Settings
from utils import Logger
import spaces, storages, metadata, groups, tokens, shares, files, filesystem

def registerSpace(base_path, directory):
    full_path = base_path + os.sep + directory.name

    # only directories should be processed
    if not os.path.isdir(full_path):
        Logger.log(1, "Space can't be created, this isn't directory %s" % base_path + os.sep + directory.name)
        return

    # test if directory contains a yaml file
    yml_file = filesystem.getMetaDataFile(directory)
    if yml_file:
        yml_content = filesystem.loadYaml(yml_file)

        # test if yaml contains space_id
        if not filesystem.yamlContainsSpaceId(yml_content):
            Logger.log(3, "Creating space from %s" % base_path + os.sep + directory.name)
            dataset_name = directory.name

            # Create storage for space
            storage_id = storages.createAndGetStorage(dataset_name, os.path.join(base_path, directory.name))

            # Create group for space
            gid = groups.createParentGroup(Settings.get().config['initialGroupId'], dataset_name)
            time.sleep(1 * Settings.get().config['sleepFactor'])

            # Create invite token for the group
            token = tokens.createInviteTokenToGroup(gid, "Invite token for " + dataset_name)
            time.sleep(1 * Settings.get().config['sleepFactor'])

            # Create a new space
            space_id = spaces.createSpaceForGroup(gid, dataset_name)
            # TODO - replace with temporary token
            support_token = tokens.createNamedTokenForUser(space_id, dataset_name, Settings.get().config['serviceUserId'])
            time.sleep(3 * Settings.get().config['sleepFactor'])

            if space_id and support_token:
                # write onedata parameters (space_id, invite_token) to file
                yaml_onedata_dict = dict()
                yaml_onedata_dict[Settings.get().config['metadataFile']['space']] = space_id
                yaml_onedata_dict[Settings.get().config['metadataFile']['inviteToken']] = token['token']
                filesystem.setValuesToYaml(yml_file, yml_content, yaml_onedata_dict)

                # set up space support on the provider
                spaces.supportSpace(support_token, Settings.get().config['implicitSpaceSize'], storage_id)
                tokens.deleteNamedToken(support_token['tokenId'])
                time.sleep(3 * Settings.get().config['sleepFactor'])

                # Create public share
                file_id = spaces.getSpace(space_id)['fileId']
                description = ""
                share = shares.createAndGetShare(dataset_name, file_id, description)

                # write onedata parameter (publicURL) to file
                filesystem.setValueToYaml(yml_file, yml_content, Settings.get().config['metadataFile']['publicURL'], share['publicUrl'])

                # Set metadata for the space
                if Settings.get().config['importMetadata']:
                    metadata.setSpaceMetadataFromYaml(space_id)

                # set up permissions
                files.setFileAttributeRecursive(file_id, Settings.get().config['initialPOSIXlikePermissions'])

                Logger.log(3, "Processing of %s done." % base_path + os.sep + directory.name)
                time.sleep(3 * Settings.get().config['sleepFactor'])
            else:
                Logger.log(1, "Error: Space for %s not created." % directory.name)
        else:
            Logger.log(4, "Space for %s not created (spaceId exists in yaml file)." % directory.name)
    else:
        Logger.log(2, "Space for %s not created (not contains yaml or no dir)." % directory.name)

# TODO - WIP
def deleteSpaceWithAllStuff(spaceId):
    Logger.log(1, "Not fully implemeted yet")
    sys.exit(1)

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
