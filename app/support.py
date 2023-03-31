import datetime
import os
import filesystem
from utils import Logger, Settings


def remove_support_primary_NOW(directory: os.DirEntry):
    print("REMOVING")


def remove_support_primary(space_id: str, yaml_file_path: str, yaml_dict: dict, directory: os.DirEntry):
    Logger.log(4, f"remove_support_primary(space_id={space_id}, directory_path={directory.path})")
    removing_time = filesystem.get_token_from_yaml(yaml_dict, "removingTime", None)

    # TODO: disable QoS and cease support for primary provider

    if not removing_time:  # file does not have removing time set, first occurrence found
        time_delta = Settings.get().TIME_UNTIL_REMOVED

        if time_delta == "never" or time_delta == "now":
            removing_time = time_delta
            removing_time_string = time_delta
        else:
            removing_time = datetime.datetime.now() + time_delta
            removing_time_string = removing_time.strftime(Settings.get().TIME_FORMATTING_STRING)

        Logger.log(2, f"Found space with id {space_id} and path {directory.path} to remove, WILL BE REMOVED {removing_time_string.upper()}!")
        # TODO: send email
    else:
        removing_time_string = removing_time
        if removing_time != "never" and removing_time != "now":
            try:
                removing_time = datetime.datetime.strptime(removing_time, Settings.get().TIME_FORMATTING_STRING)
            except ValueError:
                removing_time = "never"
                removing_time_string = "never"

    if removing_time == "never":
        filesystem.setValueToYaml(
            file_path=yaml_file_path,
            yaml_dict=yaml_dict,
            valueType="timeUntilRemove",
            value=removing_time_string
        )
        Logger.log(4, f"Space with id {space_id} not removed yet and it will be never removed")
        return

    remove = False
    if type(removing_time) == datetime.datetime:
        time_now = datetime.datetime.now()

        if removing_time > time_now:
            Logger.log(4, f"Space with id {space_id} not will be removed at {removing_time_string}")
            filesystem.setValueToYaml(
                file_path=yaml_file_path,
                yaml_dict=yaml_dict,
                valueType="RemovingTime",
                value=removing_time_string
            )
        else:
            Logger.log(4, f"Space with id {space_id} will be removed now, removed had to be at {removing_time_string}")
            remove = True

    if removing_time == "now":
        Logger.log(4, f"Space with id {space_id} will be removed now, used explicit value.")
        remove = True

    if remove:
        remove_support_primary_NOW(directory)
