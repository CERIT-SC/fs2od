import datetime
import shutil
import os
import time
from typing import Any, Union, Optional, Tuple
import ruamel.yaml
from settings import Settings
from utils import Logger, Utils
import spaces
import workflow
import support
import fnmatch
import tempfile


def scan_watched_directories(only_check: bool = False) -> None:
    """
    Goes through each directory in config file, tests if exists and if so, scans for new datasets
    If only_check is True, it just checks, if space exists, but does not create new when it does not
    """
    Logger.log(4, f"scanWatchedDirectories(only_check={only_check}):")

    for config_directory_entry in Settings.get().config["watchedDirectories"]:  # level of config file directory
        directories_to_scan = traverse_through_directories_wrapper(config_directory_entry)

        for directory in directories_to_scan:
            _scanWatchedDirectory(directory, only_check)


def traverse_through_directories_wrapper(regex_like_path: str) -> list:
    """
    This function is only wrapper (helper function) for traverse_through_directories_wrapper().
    It prepares path for this function
    """
    Logger.log(3, f"traverse_through_directories_wrapper(regex_like_path={regex_like_path})")
    # do not want empty filenames
    regex_like_path = regex_like_path.rstrip(os.sep)
    # one special occasion, the root (/) itself
    if not regex_like_path:
        regex_like_path = os.sep

    path_list = os.path.split(regex_like_path)

    return traverse_through_directories(path_list)


def traverse_through_directories(path_list: tuple) -> list:
    """
    Traverses through directories and returns directories (only directories) satisfying the pattern given in config file
    If there is no directory which satisfies pattern, returns empty list
    Warning: this function is recursive. For the folders depth higher than sys.getrecursionlimit()
    it is needed to change recursion limit using sys.setrecursionlimit(new_limit)
    """
    Logger.log(5, f"traverse_through_directories(path_list={path_list})")
    # os.sep representing root (/)
    paths = [os.sep]
    if path_list[0] != os.sep:
        paths = traverse_through_directories(os.path.split(path_list[0]))

    new_paths = []
    for path in paths:
        regex_name = path_list[1]

        for dirent in os.scandir(path):
            if fnmatch.fnmatch(dirent.name, regex_name) and os.path.isdir(dirent.path):
                new_paths.append(dirent.path)

    return new_paths


def _process_denied_providers(space_id: str, yaml_file_path: str, directory: os.DirEntry) -> bool:
    Logger.log(4, f"_process_denied_providers(space_id={space_id},yaml_path={yaml_file_path}):")

    yaml_dict = load_yaml(yaml_file_path)
    denied_providers = get_token_from_yaml(yaml_dict, "deniedProviders", default_value=None, error_message_importance=4)

    if denied_providers is None:
        return True  # it is good it is not in file

    if not denied_providers:  # empty list
        return True

    if "primary" not in denied_providers:
        return True  # TODO: yet doing nothing, need to create logic

    support.remove_support_primary(space_id, yaml_file_path, directory)

    return True


def _process_possible_space(directory: os.DirEntry, only_check: bool) -> bool:
    Logger.log(4, f"_process_possible_space(dir={directory.path},only_check={only_check}):")
    # test if directory contains a yaml file
    yml_trigger_file = get_trigger_metadata_file(directory)
    if not yml_trigger_file:
        Logger.log(4, f"Not processing directory {directory.name} (not contains yaml).")
        return False

    yml_access_info_file = get_access_info_storage_file(directory, yml_trigger_file)
    create_file_if_does_not_exist(yml_access_info_file)

    yml_metadata_file = os.path.join(directory.path, Settings.get().SEPARATE_METADATA_FILENAME)
    if os.path.exists(yml_metadata_file):
        yml_metadata_content = load_yaml(yml_metadata_file)
        removing_time = get_token_from_yaml(yml_metadata_content, "removingTime", error_message_importance=4)

        if removing_time == "removed":
            Logger.log(4, f"Not processing directory {directory.name} (support already revoked).")
            return False

    yml_content = load_yaml(yml_access_info_file)

    if yml_content is None:
        time_now = datetime.datetime.now()
        append_to_file_if_pattern_does_not_exist(
            yml_trigger_file, "^# %s.%s.%s %s:%s - This metadata file was checked by fs2od and found to be invalid$",
            (str(time_now.day), str(time_now.month), str(time_now.year), str(time_now.hour), str(time_now.minute)))
        Logger.log(3, f"YAML file {yml_trigger_file} in {directory.name} is not in a right format, skipping")

        return False

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
        yml_content = load_yaml(yml_trigger_file)
        space_id = yamlContainsSpaceId(yml_content)

    if not spaces.space_exists(space_id):
        Logger.log(3, f"SpaceID for {directory.name} found in yaml file, but does not exist anymore.")
        return False

    Logger.log(4, f"Space in {directory.name} with ID {space_id} exists, setting up continuous file import")

    # set continous file import on all spaces
    # TODO, #5 - when config['continousFileImport']['enabled'] is set to False, all import should be stopped
    time.sleep(1 * Settings.get().config["sleepFactor"])
    if Settings.get().config["continousFileImport"]["enabled"]:
        _auto_set_continuous_import(space_id, directory)
    else:
        spaces.disableContinuousImport(space_id, directory)

    if not Settings.get().USE_SEPARATE_METADATA_FILE:
        # not using metadata file so can skip next lines
        return True

    if not os.path.exists(yml_metadata_file):
        Logger.log(4, f"Not checking for removal of {directory.name} (not contains metadata file).")
        return False

    yaml_dict = load_yaml(yml_metadata_file)
    if not yaml_dict:
        Logger.log(4, f"Metadata file for space with ID {space_id} and path {directory.path} is empty. "
                      f"Not processing further")
        return False

    _process_denied_providers(space_id, yml_metadata_file, directory)

    yaml_dict = load_yaml(yml_metadata_file)
    setValueToYaml(
        file_path=yml_metadata_file,
        yaml_dict=yaml_dict,
        valueType="LastProgramRun",
        value=datetime.datetime.now().isoformat()
    )

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


def get_trigger_metadata_file(directory: os.DirEntry) -> str:
    """
    Gets metadata file based on provided directory and names of possible yaml files provided in configfile.
    If metadata file found, returns path to it, otherwise empty string.
    """
    Logger.log(4, f"get_metadata_file({directory.path})")

    for file in Settings.get().METADATA_FILES:
        metadata_file = os.path.join(directory, file)

        # check if given metadata file exists in directory
        if os.path.isfile(metadata_file):
            # check if a metadata file has been already found
            return metadata_file

    # no metadata file found
    Logger.log(4, "No file with metadata found in %s " % directory.path)
    return ""


def get_access_info_storage_file(directory: os.DirEntry, metadata_trigger_name: Optional[str]):
    """
    Returns filename, where access info should be stored
    User parses already found metadata file filename. If no file is parsed, it executes a function to find
    a triggering metadata filename
    """
    Logger.log(4, f"get_access_info_storage_file({directory.path}, {metadata_trigger_name})")
    if Settings.get().SEPARATE_METADATA_STORE_ACCESS:
        return os.path.join(directory, Settings.get().SEPARATE_METADATA_FILENAME)

    if metadata_trigger_name is None:
        return get_trigger_metadata_file(directory)

    return metadata_trigger_name


def _auto_set_continuous_import(space_id: str, directory: os.DirEntry):
    Logger.log(4, f"_auto_set_continuous_import(space_id={space_id},dir={directory.path}):")
    running_file = (
        directory.path
        + os.sep
        + Settings.get().config["continousFileImport"]["runningFileName"]
    )
    # test if directory contains running file
    if os.path.isfile(running_file):
        spaces.enableContinuousImport(space_id)
    else:
        spaces.disableContinuousImport(space_id, directory)


def setup_continuous_import(directory: os.DirEntry):
    Logger.log(4, f"setup_continuous_import({directory.path}):")
    # TODO, #6 - to be replaced by walk through files in Onedata instead of in POSIX
    if not directory.is_dir():
        Logger.log(4, f"Directory with path {directory.path} does not exist")
        return

    # test if directory contains a yaml file
    yml_trigger_file = get_trigger_metadata_file(directory)
    if not yml_trigger_file:
        Logger.log(4, f"YML file in {directory.path} does not exist")
        return

    yml_access_info_file = get_access_info_storage_file(directory, yml_trigger_file)
    create_file_if_does_not_exist(yml_access_info_file)

    yml_content = load_yaml(yml_access_info_file)
    # test if yaml contains space_id
    space_id = yamlContainsSpaceId(yml_content)
    if not space_id:
        Logger.log(4, f"Space id not found in {yml_access_info_file}")
        return

    # test if such space exists
    if not spaces.space_exists(space_id):
        Logger.log(1, "Space ID %s found in %s isn't correct." % (space_id, yml_access_info_file))
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


def create_file_if_does_not_exist(file_path: str) -> bool:
    """
    Creates file when non-existent.
    Returns True if new file was created, on errors and existing files returns False.
    """
    Logger.log(4, f"create_file_if_does_not_exist(path={file_path})")
    if os.path.exists(file_path):
        return False

    return create_file(file_path)


def create_file(file_path: str) -> bool:
    """
    Tries to create file specified by filename. If specified file exists, overwrites it.
    Returns True when file is created, otherwise False
    Possible errors: insufficient rights, maximum i-nodes count
    """
    Logger.log(4, f"create_file(path={file_path})")
    try:
        open(file_path, "w").close()
    except OSError as e:
        Logger.log(1, f"File {file_path} could not be created. Error: {e}")
        return False

    return True


def append_to_file(file_path: str, line: str) -> bool:
    """
    Tries to append to file with a specified by filename.
    Returns True when line was appended to file otherwise False
    Possible error: insufficient rights
    """
    Logger.log(4, f"append_to_file(path={file_path},line={line})")
    try:
        f = open(file_path, "a")
    except OSError as e:
        Logger.log(1, f"File {file_path} could not be opened for append. Error: {e}")
        return False

    f.write(line)
    f.close()

    return True


def load_file_contents(file_path: str, binary_mode: bool = False) -> Union[bytes, list, None]:
    """
    Reads contents of a file and returns it in desired form
    If binary_mode is False, it reads in textual mode (mode_char + t) and returns list of lines
    If binary_mode is True, it reads it in binary mode (mode_char + b) and returns all bytes
    If there is an error with opened file, function returns None
    """
    Logger.log(4, f"load_file_contents(path={file_path})")

    if not os.path.exists(file_path):
        Logger.log(1, f"File {file_path} doesn't exist.")
        return None

    try:
        if not binary_mode:
            opened_file = open(file_path, "r", encoding="UTF-8")
            data = opened_file.readlines()
        else:
            opened_file = open(file_path, "rb")
            # should return as much as possible (The Python Library Reference, Release 3.11.3, Chapter 7.2.)
            data = opened_file.read()
    except (OSError, Exception) as e:
        Logger.log(1, f"File {file_path} cannot be opened to read. Error: {e}.")
        return None
    else:
        opened_file.close()

    return data


def append_to_file_if_pattern_does_not_exist(file_path: str, user_friendly_pattern: str,
                                             replacement: Tuple[str, ...], with_newline: bool = True) -> bool:
    Logger.log(3, f"append_to_file_if_pattern_does_not_exist(path={file_path},pattern={user_friendly_pattern})")
    contents = load_file_contents(file_path)

    text_to_append = user_friendly_pattern.replace("%sss", "%s").replace("%ss", "%s")
    text_to_append, *_ = Utils.replace_regex_caret_dollar(text_to_append)
    for replaced_word in replacement:
        text_to_append = text_to_append.replace("%s", replaced_word, 1)  # only one for each %s
    text_to_append_print = text_to_append
    if with_newline:
        text_to_append += "\n"

    if contents is None:
        Logger.log(2, f"Text '{text_to_append_print}' could not be appended to file {file_path}; file cannot be opened")
        return False

    regex_pattern = Utils.user_friendly_pattern_to_regex_pattern(user_friendly_pattern)
    if Utils.does_pattern_exist_in_text(regex_pattern, "\n".join(contents), end=True):
        Logger.log(3, f"Text '{text_to_append_print}' needn't be appended to file {file_path}; already in file")
        return True

    Logger.log(4, f"Text '{text_to_append_print}' appended to file {file_path}")
    return append_to_file(file_path, text_to_append)


def load_yaml(file_path: str) -> Optional[dict]:
    """
    Loads a yaml file from file_path and returns it in a form of dictionary.
    If the file does not exist or cannot be loaded, returns an empty dict.
    If the file is not in the correct YAML format, returns None.
    """
    Logger.log(4, f"load_yaml(path={file_path})")
    stream = load_file_contents(file_path, binary_mode=True)

    # there is no need for log, log is done in load_file_contents() function
    if stream is None:
        return None

    yaml = ruamel.yaml.YAML(typ="safe")
    try:
        configuration = yaml.load(stream)
    except Exception as e:
        Logger.log(2, f"File with path {file_path} is not in valid YAML format. Error: {e}")
        return None

    # if an empty file was loaded
    if not configuration:
        configuration = dict()

    Logger.log(5, "Configuration:", pretty_print=configuration)

    return configuration


def get_token_from_yaml(yaml_dict: dict, token: str, default_value: Any = None, error_message_importance: int = 3) -> Any:
    """
    Return given token from YAML file.
    or None when file doesn't contain it.
    """
    if yaml_dict:
        onedata_part: dict = yaml_dict.get(Settings.get().config["metadataFileTags"]["onedata"])
        if onedata_part:
            return onedata_part.get(Settings.get().config["metadataFileTags"][token], default_value)

    Logger.log(error_message_importance, f"No Onedata tag, nor token '{token}' in YAML")
    return None


def convert_dict_to_yaml(dictionary: dict) -> str:
    """
    Converts dictionary object to YAML fs2od-compatible string
    On error returns empty string
    """
    Logger.log(4, f"convert_dict_to_yaml()")
    # store new yaml file
    ryaml = ruamel.yaml.YAML()
    ryaml.width = (
        200  # count of characters on a line, if there is more chars, line is broken
    )
    ryaml.indent(sequence=4, offset=2)
    with tempfile.TemporaryFile("w+", encoding="UTF-8") as temp_file:
        # this function behaves the best when writing right to file
        ryaml.dump(dictionary, temp_file)
        # must be sure that changes are written to temporary file
        temp_file.flush()
        # now, pointer to file is on position after last written character, must set it to first position in file
        temp_file.seek(0)
        # now we are reading what we have written
        yaml_string = temp_file.read()

    return yaml_string


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
        if valueType == "LastProgramRun":
            yaml_dict[Settings.get().config["metadataFileTags"]["onedata"]][
                Settings.get().config["metadataFileTags"]["lastProgramRun"]
            ] = value

        # open yaml file
        with open(file_path, "w") as f:
            f.write(convert_dict_to_yaml(yaml_dict))
    else:
        Logger.log(1, "Metadata file %s doesn't exists." % file_path)


def set_values_to_yaml(file_path: str, yaml_dict: dict, new_values_dict: dict) -> bool:
    """
    Set values to Onedata tag in yaml.
    Returns True if successful, otherwise False.
    Possible errors: metadata file does not exist, cannot write to metadata file, unexpected error
    """
    if not os.path.exists(file_path):
        Logger.log(1, f"Metadata file {file_path} doesn't exist.")
        return False

    if not yaml_dict.get(Settings.get().config["metadataFileTags"]["onedata"]):
        # there isn't tag onedata yet
        yaml_dict[Settings.get().config["metadataFileTags"]["onedata"]] = dict()

    # change value in original yaml dict
    yaml_dict[Settings.get().config["metadataFileTags"]["onedata"]] = new_values_dict

    # store new yaml file
    # Solving bad indentation of list
    # https://stackoverflow.com/questions/25108581/python-yaml-dump-bad-indentation
    # yaml.safe_dump(yaml_dict, f, sort_keys=False)
    ryaml = ruamel.yaml.YAML()
    ryaml.width = 200  # count of characters on a line, if there is more chars, line is breaked
    ryaml.indent(sequence=4, offset=2)

    try:
        # open yaml file
        with open(file_path, "w") as f:
            ryaml.dump(yaml_dict, f)
    except OSError as e:
        Logger.log(1, f"Metadata file {file_path} cannot be opened. Error: {e}")
        return False
    except Exception as e:
        Logger.log(1, f"Unexpected error with metadata file {file_path}. Error: {e}")
        return False

    return True


def remove_folder(directory: os.DirEntry) -> bool:
    """
    This operation is destructive and not reversible. Removes given folder wit its contents.
    If removal was successful, returns true, otherwise false
    """
    Logger.log(4, f"remove_folder(dir={directory.path}):")
    try:
        shutil.rmtree(directory)
    except Exception:
        return False
    else:
        return True


def chmod_recursive(path: Union[os.DirEntry, str], mode: int) -> bool:
    """
    Changes the mode of given path and its subdirectories/subfiles
    If chmod was successful, returns True, otherwise False
    """
    Logger.log(4, f"chmod_recursive(dir={path},mode={oct(mode)})")
    try:
        os.chmod(path, mode)

        for root, directories, files in os.walk(path):
            for directory in directories:
                os.chmod(os.path.join(root, directory), mode)
            for file in files:
                os.chmod(os.path.join(root, file), mode)
    except NotImplemented as e:
        Logger.log(3, f"Cannot change mode for path {path}. Not implemented. Error: {e}")
        return False
    except Exception as e:
        Logger.log(3, f"Cannot change mode for path {path}. Unknown error. Error: {e}")
        return False

    Logger.log(5, f"Mode for path {path} was changed to {oct(mode)}")

    return True


def get_dir_entry_of_directory(path: str) -> Union[os.DirEntry, None]:
    """
    This function converts path string to os.DirEntry value
    Warning: if parent directory is not readable, it has undefined behavior
    On success returns DirEntry object, otherwise None
    """
    if not os.path.isdir(os.path.join(path, "..")):
        return None

    path = path.rstrip("/")
    directory_name = os.path.basename(path)

    for dir_entry in os.scandir(os.path.join(path, "..")):
        if dir_entry.name == directory_name:
            return dir_entry

    return None

