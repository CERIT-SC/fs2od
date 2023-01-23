import os
import time
import sys
from pprint import pprint
from string import Template
from settings import Settings
from utils import Logger, Utils
import spaces, storages, metadata, groups, tokens, shares, files, filesystem, dareg


def registerSpace(base_path, directory):
    full_path = base_path + os.sep + directory.name

    # only directories should be processed
    if not os.path.isdir(full_path):
        Logger.log(
            3,
            "Space can't be created, this isn't directory %s" % base_path + os.sep + directory.name,
        )
        return

    # test if directory contains a yaml file
    yml_file = filesystem.getMetaDataFile(directory)
    if yml_file:
        yml_content = filesystem.loadYaml(yml_file)

        # test if yaml contains space_id
        if not filesystem.yamlContainsSpaceId(yml_content):
            Logger.log(3, "Creating space from %s" % base_path + os.sep + directory.name)
            dataset_name = Settings.get().config["datasetPrefix"] + directory.name

            if not Utils.isValidOnedataName(dataset_name):
                Logger.log(2, "Invalid dataset name %s" % directory.name)
                return

            # Create a new space
            space_id = spaces.createSpaceForGroup(
                Settings.get().config["managerGroupId"], dataset_name
            )
            if Settings.get().config["dareg"]["enabled"] and space_id:
                dareg.register_dataset(space_id, dataset_name, base_path)

            time.sleep(1 * Settings.get().config["sleepFactor"])

            # Create support token
            support_token = tokens.createTemporarySupportToken(space_id)

            # Create storage for the space
            storage_id = storages.createAndGetStorage(
                dataset_name, os.path.join(base_path, directory.name)
            )
            if Settings.get().config["dareg"]["enabled"] and storage_id:
                dareg.log(space_id, "info", "created storage %s" % storage_id)
            time.sleep(3 * Settings.get().config["sleepFactor"])

            if space_id and support_token:
                # set up space support on the provider
                result_support = spaces.supportSpace(
                    support_token, Settings.get().config["implicitSpaceSize"], storage_id, space_id
                )
                time.sleep(2 * Settings.get().config["sleepFactor"])

                if Settings.get().config["dareg"]["enabled"] and result_support:
                    dareg.log(space_id, "info", "supported")
                # HACK
                if not result_support:
                    # delete space
                    spaces.removeSpace(space_id)
                    time.sleep(2 * Settings.get().config["sleepFactor"])

                    # delete storage
                    storages.removeStorage(storage_id)
                    Logger.log(
                        1, "Space for %s not created (unsucessfull support)." % directory.name
                    )
                    if Settings.get().config["dareg"]["enabled"] and result_support:
                        dareg.log(space_id, "error", "removed")
                    return

                # Create user group for space
                gid = groups.createChildGroup(Settings.get().config["userGroupId"], dataset_name)
                if Settings.get().config["dareg"]["enabled"] and gid:
                    dareg.log(space_id, "info", "created group %s" % gid)
                time.sleep(1 * Settings.get().config["sleepFactor"])

                # Create invite token for the user group
                token = tokens.createInviteTokenToGroup(gid, dataset_name)
                if Settings.get().config["dareg"]["enabled"] and token:
                    dareg.log(space_id, "info", "created invite token")
                time.sleep(1 * Settings.get().config["sleepFactor"])

                # add the space to the user group
                privileges = [
                    "space_view",
                    "space_view_privileges",
                    "space_read_data",
                    "space_add_support",
                ]
                spaces.addGroupToSpace(space_id, gid, privileges)
                # TODO - test result
                if Settings.get().config["dareg"]["enabled"] and True:
                    dareg.log(space_id, "info", "group added to space")
                time.sleep(1 * Settings.get().config["sleepFactor"])

                # write onedata parameters (space_id, invite_token) to file
                yaml_onedata_dict = dict()
                yaml_onedata_dict[Settings.get().config["metadataFileTags"]["space"]] = space_id
                yaml_onedata_dict[Settings.get().config["metadataFileTags"]["inviteToken"]] = token[
                    "token"
                ]
                filesystem.setValuesToYaml(yml_file, yml_content, yaml_onedata_dict)
                time.sleep(3 * Settings.get().config["sleepFactor"])

                # first import of files to Onedata space
                spaces.startAutoStorageImport(space_id)
                time.sleep(3 * Settings.get().config["sleepFactor"])

                # set up permissions
                file_id = spaces.getSpace(space_id)["fileId"]
                files.setFileAttributeRecursive(
                    file_id, Settings.get().config["initialPOSIXlikePermissions"]
                )

                # create public share
                share = shares.createAndGetShare(dataset_name, file_id)
                if not share:
                    Logger.log(1, "Share for the space %s not created." % dataset_name)
                    return

                if Settings.get().config["dareg"]["enabled"]:
                    dareg.update_dataset(space_id, token["token"], share["publicUrl"])

                # add Share description
                with open("share_description_base.md", "r") as file:
                    to_substitute = {
                        "dataset_name": dataset_name,
                        "institution_name": Settings.get().config["institutionName"],
                        "share_file_id": share["rootFileId"],
                    }
                    src = Template(file.read())
                    result = src.substitute(to_substitute)
                    shares.updateShare(share["shareId"], description=result)

                # write onedata parameter (publicURL) to file
                filesystem.setValueToYaml(
                    yml_file,
                    yml_content,
                    Settings.get().config["metadataFileTags"]["publicURL"],
                    share["publicUrl"],
                )

                # set metadata for the space
                if Settings.get().config["importMetadata"]:
                    metadata.setSpaceMetadataFromYaml(space_id)

                path = base_path + os.sep + directory.name
                Logger.log(3, "Processing of %s done." % path)
                if Settings.get().config["dareg"]["enabled"]:
                    dareg.log(space_id, "info", "processing done")
                time.sleep(3 * Settings.get().config["sleepFactor"])
            else:
                Logger.log(1, "Space for %s not created." % directory.name)
        else:
            Logger.log(
                4, "Space for %s not created (spaceId exists in yaml file)." % directory.name
            )
    else:
        Logger.log(4, "Space for %s not created (not contains yaml or no dir)." % directory.name)


# TODO - WIP
def deleteSpaceWithAllStuff(spaceId):
    Logger.log(1, "Not fully implemeted yet")
    sys.exit(1)

    res_spaces = spaces.getSpaces()
    for s in res_spaces:
        if spaceId == s["spaceId"]:
            space_name = s["name"]

    if space_name == "211226_70SRNAP_A1":
        return

    # invite tokens
    deleted_tokens = 0
    for tokenId in tokens.listAllNamedtokens():
        token = tokens.getNamedToken(tokenId)
        if space_name in token["name"]:
            tokens.deleteNamedToken(tokenId)
            print("*** Token", token["name"], "deleted. ")
            deleted_tokens += 1
            time.sleep(0.5)

    # spaces and groups associated to given spaces
    deleted_spaces = 0
    deleted_groups = 0
    for space in spaces.getSpaces():
        if space_name in space["name"]:

            # remove group
            space_groups = spaces.listSpaceGroups(space["spaceId"])
            for groupId in space_groups:
                pprint(groups.getGroupDetails(groupId))
                group_name = groups.getGroupDetails(groupId)["name"]
                if space_name in group_name:
                    groups.removeGroup(groupId)
                    print("Group", group_name, "deleted. ")
                    deleted_groups += 1
                    time.sleep(0.5)

            spaces.removeSpace(space["spaceId"])
            print("Space", space["name"], "deleted. ")
            deleted_spaces += 1
            time.sleep(0.5)

    # storages
    time.sleep(3)  # Removing of spaces have to be propagated to Oneprovider
    deleted_storages = 0
    for storageId in storages.getStorages()["ids"]:
        storage = storages.getStorageDetails(storageId)
        if space_name in storage["name"]:
            storages.removeStorage(storageId)
            print("Storage", storage["name"], "deleted. ")
            deleted_storages += 1
            time.sleep(0.5)
