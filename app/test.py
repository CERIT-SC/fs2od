from pprint import pprint
import time
import sys
import os
from settings import Settings
from utils import Logger
import spaces, storages, groups, filesystem, tokens, oneprovider, onezone


def safetyNotice(message):
    print("*** Possibly dangerous action! ***")
    print(message)
    if input("If you yould like continue, write 'yes': ") != "yes":
        print("Exiting.")
        sys.exit(1)


def deleteAllTestInstances(prefix):
    """
    Delete all instances of a given prefix.
    """
    if not prefix:
        prefix = Settings.get().TEST_PREFIX

    safetyNotice(
        'All spaces, groups, tokens and storages with the prefix "' + prefix + '" will be deleted.'
    )

    # invite tokens
    deleted_tokens = 0
    for tokenId in tokens.listAllNamedtokens():
        token = tokens.getNamedToken(tokenId)
        if token["name"].startswith(prefix):
            tokens.deleteNamedToken(tokenId)
            print("Token", token["name"], "deleted. ")
            deleted_tokens += 1
            time.sleep(0.5)

    # spaces and groups associated to given spaces
    deleted_spaces = 0
    deleted_groups = 0
    for space in spaces.getSpaces():
        if space["name"].startswith(prefix):

            # remove group
            space_groups = spaces.listSpaceGroups(space["spaceId"])
            for groupId in space_groups:
                group_name = groups.getGroupDetails(groupId)["name"]
                if group_name.startswith(prefix):
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
        if storage["name"].startswith(prefix):
            storages.removeStorage(storageId)
            print("Storage", storage["name"], "deleted. ")
            deleted_storages += 1
            time.sleep(0.5)

    print("Spaces deleted =", deleted_spaces)
    print("Tokens deleted =", deleted_tokens)
    print("Groups deleted =", deleted_groups)
    print("Storages deleted =", deleted_storages)


def deleteAllTestGroups(prefix):
    """
    Delete all groups of a given prefix.
    """
    if not prefix:
        prefix = Settings.get().TEST_PREFIX

    safetyNotice('All groups with the prefix "' + prefix + '" will be deleted.')

    deleted_groups = 0
    user_groups = groups.listEffectiveUserGroups()
    for groupId in user_groups:
        group_name = groups.getGroupDetails(groupId)["name"]
        if group_name.startswith(prefix):
            groups.removeGroup(groupId)
            print("Group", group_name, "deleted. ")
            deleted_groups += 1
            time.sleep(0.5)

    print("Groups deleted =", deleted_groups)


def _testOnezone():
    Logger.log(4, "_testOnezone():")
    # test noauth request, test if an attribute exists
    if not "build" in onezone.getConfiguration():
        Logger.log(1, "Onezone didn't return its configuration.")
        return 1

    # test auth request
    if "error" in onezone.getCurrentUserDetails():
        Logger.log(1, "Onezone didn't respond to auth request.")
        return 2

    return 0


def _testOneprovider():
    Logger.log(4, "_testOneprovider():")
    # test noauth request, test if an attribute exists
    if not "build" in oneprovider.getConfiguration():
        Logger.log(1, "Oneprovider doesn't return its configuration.")
        return 1

    # test auth request
    if "error" in spaces.getSpaces():
        Logger.log(1, "Oneprovider doesn't respond to auth request.")
        return 2

    return 0


def testConnection():
    result = _testOnezone()
    result = result + _testOneprovider()

    if result == 0:
        Logger.log(3, "Onezone and Oneprovider exist and respond.")
    else:
        Logger.log(1, "Error when communicating with Onezone and Oneprovider.")
    return result


def scanWatchedDirectoriesToRemove():
    Logger.log(4, "scanWatchedDirectories():")

    for directory in Settings.get().config["watchedDirectories"]:
        _scanWatchedDirectoryToRemove(directory)


def _scanWatchedDirectoryToRemove(base_path):
    Logger.log(4, "_scanWatchedDirectoryToRemove(%s):" % base_path)
    Logger.log(3, "Start processing path %s" % base_path)

    if not os.path.isdir(base_path):
        Logger.log(1, "Directory %s can't be processed, it doesn't exist." % base_path)
        return

    _removingAttributesFromYaml(base_path)


def _removingAttributesFromYaml(base_path):
    Logger.log(4, "_removingAttributesFromYaml(%s):" % base_path)
    sub_dirs = os.scandir(path=base_path)
    # TODO - add condition to process only directories (no files)
    for directory in sub_dirs:
        _removeOnedataAttributes(base_path, directory)

def _removeOnedataAttributes(base_path, directory):
    full_path = base_path + os.sep + directory.name

    # only directories should be processed
    if not os.path.isdir(full_path):
        Logger.log(
            3,
            "Value can't be removed, this isn't directory %s" % base_path + os.sep + directory.name,
        )
        return

    # test if directory contains a yaml file
    yml_file = filesystem.getMetaDataFile(directory)
    if yml_file:
        yml_content = filesystem.loadYaml(yml_file)

        # test if yaml contains space_id
        if filesystem.yamlContainsSpaceId(yml_content):
            filesystem.removeValuesFromYaml(yml_file, yml_content)


def registerSpace(path):
    Logger.log(1, "Not fully implemeted yet")
    sys.exit(1)

    # if last char is os.sep(/) remove it
    if path[-1] == os.sep:
        path = path[0 : len(path) - 1]

    # split according to last os.sep char (/)
    temp = path.rsplit(os.sep, 1)
    base_path = temp[0]
    directory = temp[1]

    workflow.registerSpace(base_path, directory)
