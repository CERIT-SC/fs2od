from pprint import pprint
import time
import sys
from settings import Settings
from utils import Logger
import spaces, storages, groups, request, tokens, oneprovider, onezone, dareg


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


def _testOneprovider(oneprovider_index: int = 0):
    Logger.log(4, f"_testOneprovider(order={oneprovider_index}):")
    # test noauth request, test if an attribute exists
    if "build" not in oneprovider.getConfiguration(oneprovider_index):
        Logger.log(1, f"Oneprovider doesn't return its configuration. (order={oneprovider_index})")
        return 1

    # test auth request
    if "error" in spaces.getSpaces(oneprovider_index):
        Logger.log(1, "Oneprovider doesn't respond to auth request.")
        return 2

    return 0


def _testOneproviders(every_provider: bool = False) -> tuple:
    """
    Tests communication with each of provided Oneproviders
    """
    # defining two characteristic vectors (binary) - one for noauth request one for auth request
    # because there is a need to check them separately, ternary vector would do the job too
    # order of bits is reversed in the final vector
    vector_noauth = 0
    vector_auth = 0

    # do not want to test if replication is off
    provider_count = len(Settings.get().ONEPROVIDERS_API_URL) if \
        every_provider or Settings.get().DATA_REPLICATION_ENABLED \
        else 1

    for index in range(provider_count):
        result = _testOneprovider(index)
        # if 1, it will set 1, if 2 or 0, it will stay as is
        vector_noauth |= (result & 1)
        result >>= 1
        # if was 2, now will set to 1
        vector_auth |= result
        # shifting for the next iteration
        vector_noauth <<= 1
        vector_auth <<= 1

    return vector_noauth, vector_auth


def _test_dareg() -> int:
    Logger.log(4, f"_test_dareg():")
    if not Settings.get().DAREG_ENABLED:
        return 0

    if dareg.get_index() == b"":
        Logger.log(1, f"DAREG does not return any answer.")
        return 1

    # TODO: check auth
    return 0



def testConnection(of_each_oneprovider: bool = False):
    # testing Onezone
    result = _testOnezone()
    # testing Oneprovider(s)
    noauth, auth = _testOneproviders(of_each_oneprovider)
    # not using yet, discarding
    result = result + noauth + auth
    # testing DAREG

    result += _test_dareg()

    if result == 0:
        Logger.log(3, "Onezone, Oneprovider and DAREG, if enabled, exist and respond.")
    else:
        Logger.log(1, "Error when communicating with Onezone, Oneprovider or DAREG.")
    return result


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
