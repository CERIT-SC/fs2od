import os
import time
import sys
from pprint import pprint
from string import Template
from settings import Settings
from utils import Logger, Utils
import spaces, storages, metadata, groups, tokens, shares, files, filesystem, dareg, qos, actions_log

actions_logger = actions_log.get_actions_logger()

def _get_storage_index(space_id: str, number_of_available_storages: int) -> int:
    """
    Returns index of storage which will support the space.
    List of available storages of Oneproviders is provided in config.yml
    """
    # converting from base 18
    space_id_int = int(space_id, 18)

    # using division remainder causes uniform distribution between storages
    storage_index = space_id_int % number_of_available_storages
    return storage_index

def _add_support_from_all(support_token: str, space_id: str) -> None:
    """
    Iterates through each of the supporting providers and adds their support to space.
    """
    supporting_providers = Settings.get().config["dataReplication"]["supportingProviders"]
    for index in range(len(supporting_providers)):
        storage_ids = supporting_providers[index]["storageIds"]
        storage_id = storage_ids[_get_storage_index(space_id, len(storage_ids))]

        result_support = spaces.supportSpace(
            support_token, Settings.get().config["implicitSpaceSize"], storage_id, space_id, oneprovider_index=index + 1
        )
        time.sleep(2 * Settings.get().config["sleepFactor"])

        if Settings.get().config["dareg"]["enabled"] and result_support:
            dareg.log(space_id, "info", "supported")


def _add_qos_requirement(space_id: str, replicas_number: int):
    """
    Adds Quality of Service requirement to replicate any storage to whole space.
    """
    file_id = spaces.get_space(space_id)["fileId"]

    requirement_id = qos.add_requirement(file_id, "anyStorage", replicas_number)["qosRequirementId"]
    if requirement_id:
        Logger.log(
            3,
            "QoS requirement %s was created for space %s with %s replicas" % (space_id, requirement_id, replicas_number)
        )
    else:
        Logger.log(
            1,
            "QoS requirement could not be created for space %s" % space_id
        )


def registerSpace(base_path, directory) -> bool:
    # only directories should be processed
    full_path = base_path + os.sep + directory.name
    if not os.path.isdir(full_path):
        Logger.log(3, f"Space can't be created, this isn't directory {full_path}")
        return False

    # test if directory contains a yaml file
    yml_file = filesystem.getMetaDataFile(directory)
    if not yml_file:
        Logger.log(4, "Space for %s not created (not contains yaml or no dir)." % directory.name)
        return False

    yml_content = filesystem.loadYaml(yml_file)

    # test if yaml contains space_id
    if filesystem.yamlContainsSpaceId(yml_content):
        Logger.log(4, "Space for %s not created (spaceId exists in yaml file)." % directory.name)
        return False

    Logger.log(3, f"Creating space from {full_path}")
    dataset_name = Settings.get().config["datasetPrefix"] + directory.name

    if not Utils.isValidOnedataName(dataset_name):
        # try clear the name
        dataset_name = Utils.clearOnedataName(dataset_name)
        Logger.log(2, f"Invalid dataset name {directory.name}. Changing to {dataset_name}")

    # and test it again
    if not Utils.isValidOnedataName(dataset_name):
        Logger.log(2, f"Dataset name {directory.name} can't be cleared")
        return False

    space_name = Settings.get().TEST_PREFIX + dataset_name if Settings.get().TEST else dataset_name

    actions_logger.log_pre("space", dataset_name)
    # Create a new space
    space_id = spaces.createSpaceForGroup(
        group_id=Settings.get().config["managerGroupId"],
        space_name=space_name
    )
    actions_logger.log_post(space_id)

    if Settings.get().config["dareg"]["enabled"] and space_id:
        dareg.register_dataset(space_id, dataset_name, base_path)

    time.sleep(1 * Settings.get().config["sleepFactor"])

    # Create support token
    actions_logger.log_pre("temporary_token", "")
    support_token = tokens.createTemporarySupportToken(space_id)
    actions_logger.log_post(support_token.get("token", ""), only_check=True)

    actions_logger.log_pre("storage", dataset_name)
    # Create storage for the space
    storage_id = storages.createAndGetStorage(
        name=space_name,
        mountpoint=os.path.join(base_path, directory.name)
    )
    actions_logger.log_post(storage_id)

    if Settings.get().config["dareg"]["enabled"] and storage_id:
        dareg.log(space_id, "info", "created storage %s" % storage_id)
    time.sleep(3 * Settings.get().config["sleepFactor"])

    if not space_id or not support_token:
        Logger.log(1, "Space for %s not created." % directory.name)
        return False

    actions_logger.log_pre("space_support", "")
    # set up space support on the provider
    result_support = spaces.supportSpace(
        token=support_token,
        size=Settings.get().config["implicitSpaceSize"],
        storage_id=storage_id,
        space_id=space_id
    )
    time.sleep(2 * Settings.get().config["sleepFactor"])
    actions_logger.log_post(result_support, only_check=True)

    if Settings.get().config["dareg"]["enabled"] and result_support:
        dareg.log(space_id, "info", "supported")

    # TODO:
    if Settings.get().DATA_REPLICATION_ENABLED:
        Logger.log(
            3, "Setting up replication of space %s" % space_id
        )
        _add_support_from_all(support_token, space_id)
        _add_qos_requirement(space_id, Settings.get().DATA_REPLICATION_REPLICAS)

    # TODO: resolve in rollback
    """
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
    """

    actions_logger.log_pre("group", space_name)
    # Create user group for space
    gid = groups.createChildGroup(
        parent_group_id=Settings.get().config["userGroupId"],
        group_name=space_name
    )
    actions_logger.log_post(gid)

    if Settings.get().config["dareg"]["enabled"] and gid:
        dareg.log(space_id, "info", "created group %s" % gid)
    time.sleep(1 * Settings.get().config["sleepFactor"])

    actions_logger.log_pre("token", space_name)
    # Create invite token for the user group
    token = tokens.createInviteTokenToGroup(
        group_id=gid,
        token_name=space_name
    )
    actions_logger.log_post(token)

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

    actions_logger.log_pre("group_to_space", "")
    response = spaces.addGroupToSpace(
        space_id=space_id,
        gid=gid,
        privileges=privileges
    )
    actions_logger.log_post(response.ok, only_check=True)

    if Settings.get().config["dareg"]["enabled"] and response: # response is valid object, removed todo
        dareg.log(space_id, "info", "group added to space")
    time.sleep(1 * Settings.get().config["sleepFactor"])

    # not logging, only filesystem operation
    # write onedata parameters (space_id, invite_token) to file
    yaml_onedata_dict = dict()
    yaml_onedata_dict[Settings.get().config["metadataFileTags"]["space"]] = space_id
    yaml_onedata_dict[Settings.get().config["metadataFileTags"]["inviteToken"]] = token["token"]
    filesystem.setValuesToYaml(yml_file, yml_content, yaml_onedata_dict)
    time.sleep(3 * Settings.get().config["sleepFactor"])


    actions_logger.log_pre("auto_storage_import", "")
    # first import of files to Onedata space
    response = spaces.startAutoStorageImport(space_id)
    time.sleep(3 * Settings.get().config["sleepFactor"])
    actions_logger.log_post(response.ok, only_check=True)

    # set up permissions
    actions_logger.log_pre("file_id", "")
    file_id = spaces.get_space(space_id=space_id)["fileId"]
    actions_logger.log_post(file_id, only_check=True)

    files.setFileAttributeRecursive(
        file_id=file_id,
        posix_mode=Settings.get().config["initialPOSIXlikePermissions"]
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
