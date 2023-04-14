import datetime
import os
import filesystem
import files
import time
import spaces
import oneprovider
import transfers
from utils import Logger, Settings

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

    yaml_dict = filesystem.loadYaml(yaml_file)

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

    return completed


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

    status = filesystem.remove_folder(directory)
    Logger.log(2, f"Directory {directory.path} for space with id {space_id} removed: {status}")

    return status


def remove_support_primary(space_id: str, yaml_file_path: str, yaml_dict: dict, directory: os.DirEntry):
    Logger.log(4, f"remove_support_primary(space_id={space_id}, directory_path={directory.path})")
    removing_time = filesystem.get_token_from_yaml(yaml_dict, "removingTime", None)

    if not removing_time:  # file does not have removing time set, first occurrence found
        time_delta = Settings.get().TIME_UNTIL_REMOVED

        if time_delta == "never" or time_delta == "now":
            removing_time = time_delta
            removing_time_string = time_delta
            removing_time_log = time_delta
        else:
            removing_time = datetime.datetime.now() + time_delta
            removing_time_string = removing_time.isoformat()
            removing_time_log = removing_time.strftime(Settings.get().TIME_FORMATTING_STRING)

        Logger.log(2, f"Found space with id {space_id} and path {directory.path} to remove, "
                      f"WILL BE REMOVED {removing_time_log.upper()}!")

        # TODO: send email

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
        time_now = datetime.datetime.now()

        if removing_time > time_now:
            Logger.log(4, f"Space in {directory.name} with id {space_id} "
                          f"will be removed at {removing_time_log}, not now")
            filesystem.setValueToYaml(
                file_path=yaml_file_path,
                yaml_dict=yaml_dict,
                valueType="RemovingTime",
                value=removing_time_string
            )
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


