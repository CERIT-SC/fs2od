import datetime
import os
import string
import sys
import time
from pprint import pprint
import actions_log
import commander
import dareg
import filesystem
import groups
import language
import mail
import metadata
import qos
import shares
import spaces
import storages
import tokens
from settings import Settings
from utils import Logger, Utils

actions_logger = actions_log.get_actions_logger()

RECIPIENTS_COMMAND_MAP = commander.CommandMap({
        "to": commander.Command(mail.Recipients.add_to),
        "default": commander.Command(mail.Recipients.add_to),
        "cc": commander.Command(mail.Recipients.add_cc),
        "bcc": commander.Command(mail.Recipients.add_bcc)
})

METADATA_COMMAND_MAP = commander.CommandMap({
    "metadata": commander.Command(Utils.get_value_from_dictionary)
})


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
    supporting_providers_storages = Settings.get().ONEPROVIDERS_STORAGE_IDS

    for index in range(1, len(supporting_providers_storages)):
        storage_ids = supporting_providers_storages[index]
        storage_id = storage_ids[_get_storage_index(space_id, len(storage_ids))]

        result_support = spaces.supportSpace(
            support_token, Settings.get().config["implicitSpaceSize"], storage_id, space_id, oneprovider_index=index
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


def register_space(directory: os.DirEntry) -> bool:
    # only directories should be processed
    full_path = os.path.abspath(directory.path)
    base_path = os.path.dirname(full_path)
    if not os.path.isdir(full_path):
        Logger.log(3, f"Space can't be created, this isn't directory {full_path}")
        return False

    # test if directory contains a yaml file
    yml_trigger_file = filesystem.get_trigger_metadata_file(directory)
    if not yml_trigger_file:
        Logger.log(4, "Space for %s not created (not contains yaml or no dir)." % directory.name)
        return False

    yml_access_info_file = filesystem.get_access_info_storage_file(directory, yml_trigger_file)
    filesystem.create_file_if_does_not_exist(yml_access_info_file)

    yml_content = filesystem.load_yaml(yml_access_info_file)

    # test if yaml contains space_id
    if filesystem.yamlContainsSpaceId(yml_content):
        Logger.log(4, "Space for %s not created (spaceId exists in yaml file)." % directory.name)
        return False

    Logger.log(3, f"Creating space from {full_path}")
    dataset_name = Settings.get().config["datasetPrefix"] + directory.name

    if Settings.get().TEST:
        dataset_name = Settings.get().TEST_PREFIX + dataset_name

    if not Utils.isValidOnedataName(dataset_name):
        # try clear the name
        dataset_name_old = dataset_name
        dataset_name = Utils.clearOnedataName(dataset_name)
        Logger.log(2, f"Invalid dataset name {dataset_name_old}. Changing to {dataset_name}")

    # and test it again
    if not Utils.isValidOnedataName(dataset_name):
        Logger.log(2, f"Dataset name {directory.name} can't be cleared")
        return False

    actions_logger.new_actions_log()

    actions_logger.log_pre("space", dataset_name)
    # Create a new space
    space_id = spaces.createSpaceForGroup(
        group_id=Settings.get().config["managerGroupId"],
        space_name=dataset_name
    )
    is_ok = actions_logger.log_post(space_id)
    if not is_ok: return False

    if Settings.get().config["dareg"]["enabled"] and space_id:
        dareg.register_dataset(space_id, dataset_name, base_path)

    time.sleep(1 * Settings.get().config["sleepFactor"])

    # Create support token
    actions_logger.log_pre("temporary_token", "")
    support_token = tokens.create_temporary_support_token(space_id)
    is_ok = actions_logger.log_post(support_token, only_check=True)
    if not is_ok: return False

    actions_logger.log_pre("storage", dataset_name)
    # Create storage for the space
    storage_id = storages.create_and_get_storage(
        name=dataset_name,
        mount_point=full_path
    )
    is_ok = actions_logger.log_post(storage_id)
    if not is_ok: return False

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
    is_ok = actions_logger.log_post(result_support, only_check=True)
    if not is_ok: return False

    if Settings.get().config["dareg"]["enabled"] and result_support:
        dareg.log(space_id, "info", "supported")

    if Settings.get().DATA_REPLICATION_ENABLED:
        Logger.log(
            3, "Setting up replication of space %s" % space_id
        )
        _add_support_from_all(support_token, space_id)
        _add_qos_requirement(space_id, Settings.get().DATA_REPLICATION_REPLICAS)

    actions_logger.log_pre("group", dataset_name)
    # Create user group for space
    gid = groups.createChildGroup(
        parent_group_id=Settings.get().config["userGroupId"],
        group_name=dataset_name
    )
    is_ok = actions_logger.log_post(gid)
    if not is_ok: return False

    if Settings.get().config["dareg"]["enabled"] and gid:
        dareg.log(space_id, "info", "created group %s" % gid)
    time.sleep(1 * Settings.get().config["sleepFactor"])

    actions_logger.log_pre("token", dataset_name)
    # Create invite token for the user group
    token = tokens.createInviteTokenToGroup(
        group_id=gid,
        token_name=dataset_name
    )
    is_ok = actions_logger.log_post(token)
    if not is_ok: return False

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
    is_ok = actions_logger.log_post(response.ok, only_check=True)
    if not is_ok: return False

    if Settings.get().config["dareg"]["enabled"] and response:
        dareg.log(space_id, "info", "group added to space")
    time.sleep(1 * Settings.get().config["sleepFactor"])

    actions_logger.log_pre("information", yml_access_info_file)
    # write onedata parameters (space_id, invite_token) to file
    yaml_onedata_dict = dict()
    yaml_onedata_dict[Settings.get().config["metadataFileTags"]["onezone"]] = Settings.get().ONEZONE_HOST
    yaml_onedata_dict[Settings.get().config["metadataFileTags"]["space"]] = space_id
    yaml_onedata_dict[Settings.get().config["metadataFileTags"]["inviteToken"]] = token["token"]
    status = filesystem.set_values_to_yaml(yml_access_info_file, yml_content, yaml_onedata_dict)
    is_ok = actions_logger.log_post(status)
    if not is_ok: return False

    yml_metadata = os.path.join(directory.path, Settings.get().SEPARATE_METADATA_FILENAME)
    if Settings.get().USE_SEPARATE_METADATA_FILE:
        actions_logger.log_pre("fill_metadata_file", "")
        filesystem.create_file_if_does_not_exist(yml_metadata)
        yaml_metadata_dict = filesystem.load_yaml(yml_metadata).get("Onedata2", dict())
        yaml_metadata_dict[Settings.get().config["metadataFileTags"]["deniedProviders"]] = []
        yaml_metadata_dict[Settings.get().config["metadataFileTags"]["lastProgramRun"]] = datetime.datetime.now().isoformat()
        status = filesystem.set_values_to_yaml(yml_metadata, {}, yaml_metadata_dict)
        is_ok = actions_logger.log_post(status, only_check=True)
        if not is_ok: return False

    time.sleep(3 * Settings.get().config["sleepFactor"])

    actions_logger.log_pre("file_id", "")
    file_id = spaces.get_space(space_id=space_id)["fileId"]
    is_ok = actions_logger.log_post(file_id, only_check=True)
    if not is_ok: return False

    # create public share
    actions_logger.log_pre("share", dataset_name)
    share = shares.createAndGetShare(dataset_name, file_id)
    if not share:
        Logger.log(1, "Share for the space %s not created." % dataset_name)
        return False
    is_ok = actions_logger.log_post(share["shareId"], only_check=True)
    if not is_ok: return False

    if Settings.get().config["dareg"]["enabled"]:
        dareg.update_dataset(space_id, token["token"], share["publicUrl"])

    time.sleep(Settings.get().config["sleepFactor"])

    actions_logger.log_pre("share_description", "")
    share_description = shares.create_share_description(directory)[0]
    is_ok = actions_logger.log_post(share_description, only_check=True)
    if not is_ok: return False

    # add Share description
    actions_logger.log_pre("share_update", "")
    response = shares.updateShare(
        shid=share["shareId"],
        description=share_description
    )
    is_ok = actions_logger.log_post(response.ok, only_check=True)
    if not is_ok: return False

    # write onedata parameter (publicURL) to file
    filesystem.setValueToYaml(
        yml_access_info_file,
        yml_content,
        Settings.get().config["metadataFileTags"]["publicURL"],
        share["publicUrl"],
    )

    # set metadata for the space
    actions_logger.log_pre("space_metadata", "")
    if Settings.get().config["importMetadata"]:
        status = metadata.set_space_metadata_from_yaml(directory)
    is_ok = actions_logger.log_post(status, only_check=True)
    if not is_ok: return False

    actions_logger.log_pre("auto_storage_import", "")
    # first import of files to Onedata space
    status = spaces.startAutoStorageImport(space_id)
    time.sleep(3 * Settings.get().config["sleepFactor"])
    is_ok = actions_logger.log_post(status, only_check=True)
    if not is_ok: return False

    # set up permissions

    # actions_logger.log_pre("set_files_to_posix", "")
    # success = files.setFileAttributeRecursive(
    #     file_id=file_id,
    #     posix_mode=Settings.get().config["initialPOSIXlikePermissions"]
    # )
    # is_ok = actions_logger.log_post(success, only_check=True)
    # if not is_ok: return False

    # if Settings.get().USE_METADATA_FILE:
    #     # chmod hack, no longer can change via API
    #     filesystem.chmod_recursive(yml_metadata, Settings.get().config["initialPOSIXlikePermissions"])

    send_email_about_creation(directory, yml_access_info_file)

    path = base_path + os.sep + directory.name
    Logger.log(3, "Processing of %s done." % path)
    if Settings.get().config["dareg"]["enabled"]:
        dareg.log(space_id, "info", "processing done")
    time.sleep(3 * Settings.get().config["sleepFactor"])

    actions_logger.finish_actions_log()

    return True


# TODO - WIP
def deleteSpaceWithAllStuff(spaceId):
    Logger.log(1, "Not fully implemeted yet")
    sys.exit(1)

    res_spaces = spaces.get_all_user_spaces()
    for s in res_spaces:
        if spaceId == s["spaceId"]:
            space_name = s["name"]

    if space_name == "211226_70SRNAP_A1":
        return

    # invite tokens
    deleted_tokens = 0
    for tokenId in tokens.list_all_named_tokens():
        token = tokens.getNamedToken(tokenId)
        if space_name in token["name"]:
            tokens.deleteNamedToken(tokenId)
            print("*** Token", token["name"], "deleted. ")
            deleted_tokens += 1
            time.sleep(0.5)

    # spaces and groups associated to given spaces
    deleted_spaces = 0
    deleted_groups = 0
    for space in spaces.get_all_user_spaces():
        if space_name in space["name"]:

            # remove group
            space_groups = spaces.list_space_groups_ids(space["spaceId"])
            for groupId in space_groups:
                pprint(groups.get_group_details(groupId))
                group_name = groups.get_group_details(groupId)["name"]
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


def _prepare_recipients(directory: os.DirEntry, recipients_precursor: list) -> mail.Recipients:
    """
    Prepares recipients using data from configuration file and sometimes from metadata file.
    Recipient precursors are read from a configuration file and can contain command for processing.
    There can be a precursor, which does not contain any command; it is called a final value
    Using command mapping the commands are executed and a recipient object is prepared.
    Commands are executed in passes due to a logical diversity.
    Available commands:
    First pass:
        metadata: tells the command executor that the value should be found traversing a metadata file
    Second pass:
        to: tells the command executor, that the value should be added to recipient type "To"
        cc: tells the command executor, that the value should be added to recipient type "Cc (Carbon Copy)"
        bcc: tells the command executor, that the value should be added to recipient type "Bcc (Blind Carbon Copy)"
    The final values are then found in the Recipients object
    """
    Logger.log(4, f"_prepare_recipients(directory={directory.path})")
    yaml_trigger_file = filesystem.get_trigger_metadata_file(directory)
    yaml_dict = filesystem.load_yaml(yaml_trigger_file)

    email_list_to = []
    Logger.log(5, f"Decoding data using metadata command, number of entries: {len(recipients_precursor)}")
    for address_command in recipients_precursor:
        command_result = commander.execute_command(address_command, METADATA_COMMAND_MAP, dictionary=yaml_dict)
        if command_result:
            email_list_to.append(command_result)
    Logger.log(5, f"Finished decoding using metadata command, number of recipients: {len(email_list_to)}")

    Logger.log(5, f"Decoding data using recipient types commands")
    recipients = mail.Recipients([], [], [])  # defining empty recipients
    for address_command in email_list_to:
        commander.execute_command(address_command, RECIPIENTS_COMMAND_MAP, self_object=recipients)
    Logger.log(5, f"Finished decoding data using recipient types commands")

    return recipients


def send_email_with_contents(content_filenames: tuple[str, str], to_substitute: dict, recipients: mail.Recipients):
    """
    Sends email using content given by arguments.

    content_filenames is a tuple containing string names of plain text and html template files respectively
    to_substitute is already prepared dictionary with values to substitute in templates
    recipients is a recipients object telling where to send given email
    """
    Logger.log(4, f"send_email_with_contents(content={content_filenames})")

    text_filename, html_filename = content_filenames
    template_text = filesystem.load_file_contents(text_filename)
    template_html = filesystem.load_file_contents(html_filename)
    if not template_text or not template_html:
        return

    template = string.Template("".join(template_text))
    template_h = string.Template("".join(template_html))

    result_text = template.substitute(to_substitute)
    result_html = template_h.substitute(to_substitute)

    mail.send_using_creds(
        message=result_text,
        html_message=result_html,
        credentials=Settings.get().MESSAGING.email_creds,
        recipients=recipients
    )


def send_email_about_deletion(space_id: str, directory: os.DirEntry, removing_time: str, yaml_file_path: str):
    """
    Sends email about deletion (when a space is about to be deleted)
    """
    Logger.log(3, f"send_email_about_deletion(id={space_id}, directory={directory.path})")
    deletion_text_file = language.get_filename_by_localization("deletion.txt")
    deletion_html_file = language.get_filename_by_localization("deletion.html")
    to_substitute = {
        "space_name": directory.name,
        "space_id": space_id,
        "space_path": directory.path,
        "date": removing_time,
        "config_file": os.path.basename(yaml_file_path),
        "now": datetime.datetime.now().strftime(Settings.get().TIME_FORMATTING_STRING)
    }
    recipients = _prepare_recipients(directory, Settings.get().MESSAGING.email.to.space_deletion)

    send_email_with_contents((deletion_text_file, deletion_html_file), to_substitute, recipients)


def send_email_about_creation(directory: os.DirEntry, yml_access_info_file: str):
    """
    Sends email about creation (when a space is created)
    """
    Logger.log(3, f"send_email_about_creation(directory={directory.path})")
    creation_text_file = language.get_filename_by_localization("creation.txt")
    creation_html_file = language.get_filename_by_localization("creation.html")

    yaml_dict = filesystem.load_yaml(yml_access_info_file)

    to_substitute = {
        "space_name": directory.name,
        "space_id": filesystem.get_token_from_yaml(yaml_dict, "space"),
        "space_path": directory.path,
        "onezone_url": filesystem.get_token_from_yaml(yaml_dict, "onezone"),
        "public_url": filesystem.get_token_from_yaml(yaml_dict, "publicURL"),
        "invite_token": filesystem.get_token_from_yaml(yaml_dict, "inviteToken"),
        "now": datetime.datetime.now().strftime(Settings.get().TIME_FORMATTING_STRING)
    }
    recipients = _prepare_recipients(directory, Settings.get().MESSAGING.email.to.space_creation)

    send_email_with_contents((creation_text_file, creation_html_file), to_substitute, recipients)
