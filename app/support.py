import datetime
import os
import string
import filesystem
import files
import time
import spaces
import oneprovider
import transfers
from utils import Logger, Settings, Utils
from messaging import mail

MAX_TRANSFER_COMPLETED_CHECKS = 10


def _remove_running_file_if_existent(space_id: str, directory: os.DirEntry) -> bool:
    """
    Removes file responsible for auto continuous import.
    If file was removed, returns True.
    When did not exist or could not have been removed, returns False
    """
    Logger.log(4, f"_remove_running_file_if_existent(space_id={space_id},directory_path={directory.path})")
    continuous_file_import_file = os.path.join(
        directory,
        Settings.get().config["continousFileImport"]["runningFileName"]
    )
    if not os.path.isfile(continuous_file_import_file):
        return False

    Logger.log(4, f"Running file in {directory.path} found. Removing it and disabling auto continuous import. "
                  f"Removing this dataset will be done in the next run.")
    try:
        os.remove(continuous_file_import_file)
    except Exception:
        Logger.log(4, f"Running file in directory {directory.path} could not be removed. "
                      f"To preserve data complete, removing will no execute.")
        return False

    return True


def _remove_directory_from_filesystem(directory: os.DirEntry) -> bool:
    try:
        filesystem.remove_folder(directory)
    except Exception:
        Logger.log(2, f"Directory on {directory.path} cannot be removed.")
        return False
    else:
        Logger.log(2, f"Directory on {directory.path} was removed.")
        return True


def _wait_for_transfers_to_complete(space_id: str, transfers_ids: list) -> bool:
    completed = False
    for try_index in range(MAX_TRANSFER_COMPLETED_CHECKS):
        time.sleep(15 * Settings.get().config["sleepFactor"])
        Logger.log(5, f"Checking for completed transfers, try {try_index + 1}/{MAX_TRANSFER_COMPLETED_CHECKS}.")

        for transfer_index in range(len(transfers_ids) - 1, -1, -1):  # going down for easier removal from list
            status_dict = transfers.get_transfer_status(
                transfer_id=transfers_ids[transfer_index],
                status_type_if_not_found="replicationStatus"
            )

            # transfer should be here, because was created few seconds ago. If not, internal error
            if not status_dict or "replicationStatus" not in status_dict:
                Logger.log(3, f"There was a problem with transfer of id {transfers_ids[transfer_index]} "
                              f"for space with id {space_id}, not processing further.")
                transfers_ids.pop(transfer_index)

            replication_status = status_dict["replicationStatus"]
            Logger.log(5, f"Status of transfer with id {transfers_ids[transfer_index]}: {replication_status}")
            if replication_status == "failed":
                Logger.log(3,
                           f"Status of transfer with id {transfers_ids[transfer_index]} for space with id {space_id} "
                           f"failed and file dont should have not to be synced.")

            if replication_status in ("skipped", "completed", "cancelled", "failed", "not_found"):
                transfers_ids.pop(transfer_index)

        if not transfers_ids:  # all transfers were completed
            Logger.log(5, f"All transfers for space with id {space_id} were completed.")
            completed = True
            break

    return completed


def _transfer_file_to_providers(file_id: str, provider_ids: list, path_to_file: str):
    transfers_ids = []

    for provider_id in provider_ids:
        Logger.log(5, f"Trying to transfer {path_to_file} to provider with id {provider_id}.")
        transfer_info = transfers.createTransfer(
            type="replication",
            replicating_provider_id=provider_id,
            dataSourceType="file",
            file_id=file_id
        )
        if not transfer_info:
            Logger.log(3, f"Transfer of {path_to_file} to provider with id {provider_id} "
                          f"not successful.")
            continue

        Logger.log(5, f"Transfer of {path_to_file} to provider with id {provider_id} started.")
        transfers_ids.append(transfer_info["transferId"])

    time.sleep(5 * Settings.get().config["sleepFactor"])

    return transfers_ids


def _sync_information_about_space_removal(space_id: str, directory: os.DirEntry) -> bool:
    Logger.log(4, f"_sync_information_about_space_removal(space_id={space_id},directory_path={directory.path})")
    # test if directory contains a yaml file
    yaml_file = filesystem.getMetaDataFile(directory)
    if not yaml_file:
        Logger.log(4, f"Not removing space in {directory.path} with id {space_id} (not contains yaml).")
        return False

    # getting space information from provider
    space_information = spaces.get_space(space_id)
    if not space_information or "fileId" not in space_information or "providers" not in space_information:
        Logger.log(4, f"Not removing space in {directory.path} with id {space_id} (cannot connect to Oneprovider).")
        return False

    space_file_id = space_information["fileId"]
    config_file_name = os.path.basename(yaml_file)

    # file_id = files.lookup_file_id(space_name + "/" + config_file_name)
    # not using it anymore, problem when two datasets with the same name

    file_id = files.get_id_of_file_in_directory(
        directory_file_id=space_file_id,
        searched_file_name=config_file_name
    )

    if not file_id:
        Logger.log(4, f"Not removing space in {directory.path} with id {space_id} (file ID was not provided).")
        return False

    provider_ids = [provider["providerId"] for provider in space_information["providers"]]

    primary_provider_info = oneprovider.get_configuration()
    if not primary_provider_info or "providerId" not in primary_provider_info:
        Logger.log(4, f"Not removing space in {directory.path} with id {space_id} "
                      f"(cannot connect to primary Oneprovider).")
        return False

    primary_provider_id = primary_provider_info["providerId"]

    if primary_provider_id not in provider_ids:  # support was removed, but space is still present
        Logger.log(4, f"Trying to remove {directory.path} which is not supported by primary provider.")
        return _remove_directory_from_filesystem(directory)

    provider_ids.remove(primary_provider_id)

    # finding out if did not get processed before
    # if so, trying to check if there are running transfers
    # if so, tries to delete in another run, if no, removes straightly
    removing_time = filesystem.get_token_from_yaml(yaml_dict, "removingTime", None)
    if removing_time == "transfers":
        transfers_ids = transfers.get_all_transfer_ids(space_id)
        completed = _wait_for_transfers_to_complete(space_id, transfers_ids)

        # thinking about situation, when will not be removed from filesystem, but we need to keep the system integrity
        if completed:
            os.remove(yaml_file)

        return completed

    # now, there is everything prepared for removal, starting to edit filesystem

    filesystem.setValueToYaml(  # store information about space removal
        file_path=yaml_file,
        yaml_dict=yaml_dict,
        valueType="RemovingTime",
        value="removed"
    )

    status = spaces.startAutoStorageImport(space_id)  # sync information about space removal

    if not status:
        Logger.log(4, f"Space in {directory.path} with id {space_id} could not be synced, not removing.")
        filesystem.setValueToYaml(  # store information about space removal
            file_path=yaml_file,
            yaml_dict=yaml_dict,
            valueType="RemovingTime",
            value="now"
        )
        return False

    time.sleep(3 * Settings.get().config["sleepFactor"])

    transfers_ids = _transfer_file_to_providers(file_id, provider_ids, yaml_file)

    completed = _wait_for_transfers_to_complete(space_id, transfers_ids)

    if not completed:
        # if not all transfers were completed, not storing transfer ids, but in next run waiting to complete all
        # redoing all transfers again can cause congestion, because in each run there are n new transfers where
        # n = number of supporting providers
        # only checking if every transfer is completed
        filesystem.setValueToYaml(
            file_path=yaml_file,
            yaml_dict=yaml_dict,
            valueType="RemovingTime",
            value="transfers"
        )
    else:
        os.remove(yaml_file)

    return completed


def _get_filename_by_localization(filename: str) -> str:
    """
    Returns file name extended with localization. If localized file does not exist, returns given file.
    If given file does not exist, returns it with error in log
    """
    Logger.log(4, f"_get_filename_by_localization(filename={filename})")

    if not os.path.exists(filename):
        Logger.log(1, f"File with name {filename} does not exist, returning with possibility of crashing the program.")
        return filename

    language_extension = Settings.get().MESSAGING.email.language  # nothing if default, .ex when other
    filename_list = filename.split(".")

    if len(filename_list) == 1:
        filename_list[0] += language_extension
        return filename_list[0]

    filename_list[-2] += language_extension

    new_filename = ".".join(filename_list)
    if os.path.exists(new_filename):
        return new_filename

    return filename


def _send_email_about_deletion(space_id: str, directory: os.DirEntry, removing_time: str, yaml_file_path: str):
    Logger.log(4, f"_send_email_about_deletion(space_id={space_id},dir={directory.path},removing_time={removing_time})")
    deletion_text_file = _get_filename_by_localization("templates/deletion.txt")
    deletion_html_file = _get_filename_by_localization("templates/deletion.html")
    with open(deletion_text_file, "r", encoding="utf-8") as f:
        template_text = f.read()
    with open(deletion_html_file, "r", encoding="utf-8") as f:
        template_html = f.read()
    template = string.Template(template_text)
    template_h = string.Template(template_html)
    to_substitute = {
        "space_name": directory.name,
        "space_id": space_id,
        "space_path": directory.path,
        "date": removing_time,
        "config_file": os.path.basename(yaml_file_path),
        "now": datetime.datetime.now().strftime(Settings.get().TIME_FORMATTING_STRING)
    }
    result_text = template.substitute(to_substitute)
    result_html = template_h.substitute(to_substitute)

    mail.send_using_creds(
        message=result_text,
        html_message=result_html,
        credentials=Settings.get().MESSAGING.email_creds,
        email_info=Settings.get().MESSAGING.email
    )


def remove_support_primary_NOW(space_id: str, directory: os.DirEntry) -> bool:
    Logger.log(3, f"remove_support_primary_now(space_id={space_id},directory_path={directory.path})")
    # not disabling or removing QoS because revoking support of provider is possible even when QoS is set

    status = _sync_information_about_space_removal(space_id, directory)
    if not status:
        Logger.log(2, f"Could not sync config file with all supporting providers for space with id {space_id}, "
                      f"not removing.")
        return False

    status = spaces.revoke_space_support(space_id)  # ceasing/revoking support for primary provider
    if not status:
        Logger.log(2, f"Could not revoke space support for space with id {space_id}."
                      f"Continuing anyway, because it will not influence replication.")

    if Settings.get().REMOVE_FROM_FILESYSTEM:
        status = filesystem.remove_folder(directory)
        Logger.log(2, f"Directory {directory.path} for space with id {space_id} removed: {status}")
    else:
        Logger.log(2, f"Support of primary provider for space with id {space_id} in {directory.path} was revoked, "
                      f"but dataset was not removed from filesystem as set in configuration file")

    return status


def remove_support_primary(space_id: str, yaml_file_path: str, directory: os.DirEntry):
    Logger.log(4, f"remove_support_primary(space_id={space_id}, yaml_path={yaml_file_path}, "
                  f"directory_path={directory.path})")
    time_default = datetime.datetime(1900, 1, 1)
    time_now = datetime.datetime.now()
    email_sent = False

    yaml_dict = filesystem.loadYaml(yaml_file_path)
    last_program_run_time = filesystem.get_token_from_yaml(yaml_dict, "lastProgramRun", None)

    if not last_program_run_time:
        last_program_run_time = time_default
    else:
        try:
            last_program_run_time = datetime.datetime.fromisoformat(last_program_run_time)
        except ValueError:
            last_program_run_time = time_default

    removing_time = filesystem.get_token_from_yaml(yaml_dict, "removingTime", None)

    if not removing_time:  # file does not have removing time set, first occurrence found
        time_delta = Settings.get().TIME_UNTIL_REMOVED

        if time_delta == "never" or time_delta == "now":
            removing_time = time_delta
            removing_time_string = time_delta
            removing_time_log = time_delta
        else:
            removing_time = time_now + time_delta
            removing_time_string = removing_time.isoformat()
            removing_time_log = removing_time.strftime(Settings.get().TIME_FORMATTING_STRING)

        Logger.log(2, f"Found space with id {space_id} and path {directory.path} to remove, "
                      f"WILL BE REMOVED {removing_time_log.upper()}!")

        _send_email_about_deletion(space_id, directory, removing_time_log, yaml_file_path)
        email_sent = True

        status = spaces.startAutoStorageImport(space_id)  # to be sure that SPA.yml file will be synced
        if not status:
            Logger.log(2, f"Config file for space {directory.path} and id {space_id} was not synced with Onedata"
                          f" after adding removing time parameter.")
    else:
        # skipping all checks because it was previously set by our program and all checks were preformed
        if removing_time == "transfers":
            remove_support_primary_NOW(space_id, directory)
            return

        removing_time_string = removing_time
        removing_time_log = removing_time
        if removing_time != "never" and removing_time != "now":
            try:
                removing_time = datetime.datetime.fromisoformat(removing_time)
                removing_time_log = removing_time.strftime(Settings.get().TIME_FORMATTING_STRING)
            except ValueError:
                removing_time = "never"
                removing_time_string = "never"
                removing_time_log = "never"

    if removing_time == "never":
        filesystem.setValueToYaml(
            file_path=yaml_file_path,
            yaml_dict=yaml_dict,
            valueType="RemovingTime",
            value=removing_time_string
        )
        Logger.log(4, f"Space in {directory.name} with id {space_id} not removed yet and it will be never removed")
        return

    remove = False
    if type(removing_time) == datetime.datetime:
        if removing_time > time_now:
            Logger.log(4, f"Space in {directory.name} with id {space_id} "
                          f"will be removed at {removing_time_log}, not now")
            filesystem.setValueToYaml(
                file_path=yaml_file_path,
                yaml_dict=yaml_dict,
                valueType="RemovingTime",
                value=removing_time_string
            )
            is_time_for_email = Utils.is_time_for_action(
                previous_perform_time=last_program_run_time,
                time_until=removing_time,
                intervals=Settings.get().MESSAGING.email.time_before_action,
                response_on_weird_condition=True
            )
            if is_time_for_email and not email_sent:
                _send_email_about_deletion(space_id, directory, removing_time_log, yaml_file_path)

        else:
            Logger.log(4, f"Space with id {space_id} will be removed now, should have been at {removing_time_log}")
            remove = True

    if removing_time == "now":
        Logger.log(4, f"Space with id {space_id} will be removed now, used explicit value.")
        remove = True

    if remove:
        removed_running = _remove_running_file_if_existent(space_id, directory)
        if removed_running:
            Logger.log(4, f"Running file for {directory.path} was removed, removing directory will be done in next run.")
            spaces.disableContinuousImport(space_id)
            return

        remove_support_primary_NOW(space_id, directory)


