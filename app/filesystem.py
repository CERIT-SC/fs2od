import shutil
from pprint import pprint
import os
import time
from typing import Any
import ruamel.yaml
from settings import Settings
from utils import Logger
import spaces
import workflow
import support


def scanWatchedDirectories(only_check: bool = False) -> None:
    """
    Goes through each directory in config file, tests if exists and if so, scans for new datasets
    """
    Logger.log(4, "scanWatchedDirectories():")

    for directory in Settings.get().config["watchedDirectories"]:  # level of config file directory
        _scanWatchedDirectory(directory, only_check)


def _process_denied_providers(space_id: str, yaml_file_path: str, yaml_dict: dict, directory: os.DirEntry) -> bool:
    denied_providers = get_token_from_yaml(yaml_dict, "deniedProviders", None)

    if denied_providers is None:
        return True  # it is good it is not in file

    if not denied_providers:  # empty list
        return True

    if "primary" not in denied_providers:
        return True  # TODO: yet doing nothing, need to create logic

    support.remove_support_primary(space_id, yaml_file_path, yaml_dict, directory)


def _process_possible_space(directory: os.DirEntry, only_check: bool) -> bool:
    # test if directory contains a yaml file
    yml_file = getMetaDataFile(directory)
    if not yml_file:
        Logger.log(4, f"Not processing directory {directory.name} (not contains yaml).")
        return False

    yml_content = loadYaml(yml_file)
    space_id = yamlContainsSpaceId(yml_content)

    # test if yaml contains space_id, if no, create new space
    if not space_id:
        if only_check:
            Logger.log(3,
                       f"Checked for SpaceID in {directory.name}, not found in yaml, only_check was enabled, skipping")
            return True

        #  creating space, if everything goes good, status should be true
        status = workflow.register_space(directory)
        if not status:
            # if no status, enough info was provided by registerSpace, not logging more
            return False

        # after creating space, asking for information one more time
        yml_content = loadYaml(yml_file)
        space_id = yamlContainsSpaceId(yml_content)

    if not spaces.space_exists(space_id):
        Logger.log(3, "SpaceID for %s found in yaml file, but does not exist anymore." % directory.name)
        return False

    Logger.log(4, f"Space in {directory.name} with ID {space_id} exists, setting up continuous file import")

    # set continous file import on all spaces
    # TODO, #5 - when config['continousFileImport']['enabled'] is set to False, all import should be stopped
    time.sleep(1 * Settings.get().config["sleepFactor"])
    if Settings.get().config["continousFileImport"]["enabled"]:
        _auto_set_continuous_import(space_id, directory)
    else:
        spaces.disableContinuousImport(space_id)

    _process_denied_providers(space_id, yml_file, yml_content, directory)

    return True


def _scanWatchedDirectory(base_path: str, only_check: bool) -> None:
    """
    Scan if directory contains subdirectories which can be processed
    """
    Logger.log(4, "_scanWatchedDirectory(%s):" % base_path)
    Logger.log(3, "Start processing path %s" % base_path)

    if not os.path.isdir(base_path):
        Logger.log(1, "Directory %s can't be processed, it doesn't exist." % base_path)
        return

    directory_items = os.scandir(path=base_path)
    for directory_item in directory_items:
        #  checks if this item is a directory or file, if it is file , not interesting for us
        if not os.path.isdir(directory_item):
            Logger.log(4, f"Skipping item, because it is a file {directory_item.path}")
            continue

        _process_possible_space(directory_item, only_check)

    Logger.log(3, "Finish processing path %s" % base_path)


def getMetaDataFile(directory: os.DirEntry) -> str:
    """
    Gets metadata file based on provided directory and names of possible yaml files provided in configfile.
    If metadata file found, returns path to it, otherwise empty string.
    """
    Logger.log(4, "getMetaDataFile(%s):" % directory.path)
    for file in Settings.get().config["metadataFiles"]:
        yml_file = directory.path + os.sep + file
        # check if given metadata file exists in directory
        if os.path.isfile(yml_file):
            # check if a metadata file has been already found
            return yml_file

    # no metadata file found
    Logger.log(4, "No file with metadata found in %s " % directory.path)
    return ""


def _auto_set_continuous_import(space_id: str, directory: os.DirEntry):
    running_file = (
        directory.path
        + os.sep
        + Settings.get().config["continousFileImport"]["runningFileName"]
    )
    # test if directory contains running file
    if os.path.isfile(running_file):
        spaces.enableContinuousImport(space_id)
    else:
        spaces.disableContinuousImport(space_id)


def setup_continuous_import(directory: os.DirEntry):
    Logger.log(4, "setupContinuousImport(%s):" % directory.path)
    # TODO, #6 - to be replaced by walk through files in Onedata instead of in POSIX
    if not directory.is_dir():
        Logger.log(4, f"Directory with path {directory.path} does not exist")
        return

    # test if directory contains a yaml file
    yml_file = getMetaDataFile(directory)
    if not yml_file:
        Logger.log(4, f"YML file in {directory.path} does not exist")
        return

    yml_content = loadYaml(yml_file)
    # test if yaml contains space_id
    space_id = yamlContainsSpaceId(yml_content)
    if not space_id:
        Logger.log(4, f"Space id not found in {yml_file}")
        return

    # test if such space exists
    if not spaces.space_exists(space_id):
        Logger.log(1, "Space ID %s found in %s isn't correct." % (space_id, yml_file))
        return

    _auto_set_continuous_import(space_id, directory)


def yamlContainsSpaceId(yml_content: dict) -> str:
    """
    Test if yaml contains space_id.
    If so, returns it, otherwise returns empty string.
    """
    yml_spa_space_id = get_token_from_yaml(yml_content, "space")
    if not yml_spa_space_id:
        return ""
    else:
        return yml_spa_space_id


def loadYaml(file_path: str) -> dict:
    """
    Loads yaml file from file_path and returns it in form of dictionary.
    If file does not exist or cannot be loaded, returns empty dict.
    """
    if not os.path.exists(file_path):
        Logger.log(1, "File %s doesn't exists." % file_path)
        return dict()

    with open(file_path, "r") as stream:
        # configuration = yaml.safe_load(stream) # pyyaml
        yaml = ruamel.yaml.YAML(typ="safe")
        configuration = yaml.load(stream)
        # if load empty file
        if not configuration:
            configuration = dict()

        Logger.log(5, "Configuration:", pretty_print=configuration)

    return configuration


def get_token_from_yaml(yaml_dict: dict, token: str, default_value: Any = None) -> Any:
    """
    Return space_id from YAML file.
    or None when file doesn't contain it.
    """
    if yaml_dict:
        onedata_part: dict = yaml_dict.get(Settings.get().config["metadataFileTags"]["onedata"])
        if onedata_part:
            return onedata_part.get(Settings.get().config["metadataFileTags"][token], default_value)

    Logger.log(3, "No onedata tag in YAML")
    return None


def setValueToYaml(file_path, yaml_dict, valueType, value):
    if os.path.exists(file_path):
        if yaml_dict.get(Settings.get().config["metadataFileTags"]["onedata"]) == None:
            yaml_dict[Settings.get().config["metadataFileTags"]["onedata"]] = dict()

        # change value in original yaml dict
        if valueType == "Space":
            yaml_dict[Settings.get().config["metadataFileTags"]["onedata"]][
                Settings.get().config["metadataFileTags"]["space"]
            ] = value
        if valueType == "PublicURL":
            yaml_dict[Settings.get().config["metadataFileTags"]["onedata"]][
                Settings.get().config["metadataFileTags"]["publicURL"]
            ] = value
        if valueType == "InviteToken":
            yaml_dict[Settings.get().config["metadataFileTags"]["onedata"]][
                Settings.get().config["metadataFileTags"]["inviteToken"]
            ] = value
        if valueType == "DeniedProviders":
            yaml_dict[Settings.get().config["metadataFileTags"]["onedata"]][
                Settings.get().config["metadataFileTags"]["deniedProviders"]
            ] = value
        if valueType == "RemovingTime":
            yaml_dict[Settings.get().config["metadataFileTags"]["onedata"]][
                Settings.get().config["metadataFileTags"]["removingTime"]
            ] = value

        # open yaml file
        with open(file_path, "w") as f:
            # store new yaml file
            ryaml = ruamel.yaml.YAML()
            ryaml.width = (
                200  # count of characters on a line, if there is more chars, line is breaked
            )
            ryaml.indent(sequence=4, offset=2)
            ryaml.dump(yaml_dict, f)
    else:
        Logger.log(1, "Metadata file %s doesn't exists." % file_path)


def setValuesToYaml(file_path, yaml_dict, new_values_dict):
    """
    Set values to onedata tag in yaml.
    """
    if os.path.exists(file_path):
        if not yaml_dict.get(Settings.get().config["metadataFileTags"]["onedata"]):
            # there isn't tag onedata yet
            yaml_dict[Settings.get().config["metadataFileTags"]["onedata"]] = dict()

        # change value in original yaml dict
        yaml_dict[Settings.get().config["metadataFileTags"]["onedata"]] = new_values_dict

        # open yaml file
        with open(file_path, "w") as f:
            # store new yaml file
            # Solving bad indentation of list
            # https://stackoverflow.com/questions/25108581/python-yaml-dump-bad-indentation
            # yaml.safe_dump(yaml_dict, f, sort_keys=False)

            ryaml = ruamel.yaml.YAML()
            ryaml.width = (
                200  # count of characters on a line, if there is more chars, line is breaked
            )
            ryaml.indent(sequence=4, offset=2)
            ryaml.dump(yaml_dict, f)
    else:
        Logger.log(1, "Metadata file doesn't exists." % file_path)


def remove_folder(directory: os.DirEntry) -> bool:
    """
    This operation is destructive and not reversible. Removes given folder wit its contents.
    If removal was successful, returns true, otherwise false
    """
    try:
        shutil.rmtree(directory)
    except Exception:
        return False
    else:
        return True
