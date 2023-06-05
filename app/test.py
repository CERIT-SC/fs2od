import argparse
import os
import sys
import time
from typing import Optional, List
import dareg
import groups
import mail
import oneprovider
import onezone
import spaces
import storages
import tokens
from settings import Settings
from utils import Logger


class Arguments:
    def __init__(self, starting_with: str, provider: str, has_more_providers: bool = False):
        self.starting_with: str = starting_with
        self.provider: str = provider
        self.has_more_providers: bool = has_more_providers
        self.spaces: bool = False
        self.storages: bool = False
        self.tokens: bool = False
        self.groups: bool = False

    def set_all(self):
        self.spaces = True
        self.storages = True
        self.tokens = True
        self.groups = True

    def set_spaces(self):
        self.spaces = True

    def set_storages(self):
        self.storages = True

    def set_tokens(self):
        self.tokens = True

    def set_groups(self):
        self.groups = True


class InstanceType:
    space = 1
    storage = 2
    token = 4
    group = 8
    space_oz = 16  # onezone space


def print_safety_notice(message: str):
    print("*** Possibly dangerous action! ***")
    print(message)
    if input("If you yould like continue, write 'yes': ") != "yes":
        print("Action not confirmed. Exiting.")
        sys.exit(1)


def process_args(args: argparse.Namespace) -> Optional[Arguments]:
    if not args.of_provider and args.with_more_providers:
        print("Error: used argument --with_more_providers without usage --of_provider PROVIDER")
        return None

    starting_with = Settings.get().TEST_PREFIX
    if args.starting_with is not None:
        starting_with = args.starting_with

    arguments = Arguments(starting_with, args.of_provider, args.with_more_providers)

    if "all" not in vars(args):  # called without all
        arguments.set_all()
        return arguments

    if args.all:
        arguments.set_all()
        return arguments

    count_of_types = 0

    if args.spaces:
        count_of_types += 1
        arguments.set_spaces()

    if args.storages:
        count_of_types += 1
        arguments.set_storages()

    if args.tokens:
        count_of_types += 1
        arguments.set_tokens()

    if args.groups:
        count_of_types += 1
        arguments.set_groups()

    if count_of_types == 0:
        arguments.set_all()

    return arguments


def get_requested_instances_from_onezone(arguments: Arguments) -> List[tuple]:
    provider_id = onezone.resolve_provider_id_from_id_or_hostname(arguments.provider)

    if not provider_id:
        Logger.log(1, f"Provider with hostname or id {arguments.provider} not found")
        return []

    provider_spaces = onezone.get_providers_supported_spaces_from_onezone(provider_id)

    available_spaces = []
    for provider_space_id in provider_spaces:
        space_details = spaces.get_space_from_onezone(provider_space_id)
        if not space_details:
            continue

        if not arguments.has_more_providers and len(space_details["providers"]) > 1:
            continue

        if not space_details["name"].startswith(arguments.starting_with):
            continue

        available_spaces.append((InstanceType.space_oz, provider_space_id, space_details["name"]))

    return available_spaces


def get_tokens_starting_with(arguments: Arguments) -> List[tuple]:
    wanted_instances = []
    for token_id in tokens.listAllNamedtokens():
        token = tokens.getNamedToken(token_id)
        if not token["name"].startswith(arguments.starting_with):
            continue

        wanted_instances.append((InstanceType.token, token_id, token["name"]))

    return wanted_instances


def get_storages_starting_with(arguments: Arguments) -> List[tuple]:
    wanted_instances = []
    for storage_id in storages.getStorages()["ids"]:
        storage = storages.getStorageDetails(storage_id)
        if not storage["name"].startswith(arguments.starting_with):
            continue

        wanted_instances.append((InstanceType.storage, storage_id, storage["name"]))

    return wanted_instances


def get_all_users_groups_starting_with(arguments: Arguments) -> List[tuple]:
    wanted_instances = []

    user_groups = groups.listEffectiveUserGroups()
    for group_id in user_groups:
        group_name = groups.getGroupDetails(group_id)["name"]
        if not group_name.startswith(arguments.starting_with):
            continue

        wanted_instances.append((InstanceType.group, group_id, group_name))

    return wanted_instances


def get_only_groups_under_spaces_starting_with(arguments: Arguments) -> List[tuple]:
    wanted_instances = []
    for space in spaces.getSpaces():
        space_groups = spaces.listSpaceGroups(space["spaceId"])
        for group_id in space_groups:
            group_name = groups.getGroupDetails(group_id)["name"]

            if not group_name.startswith(arguments.starting_with):
                continue

            wanted_instances.append((InstanceType.group, group_id, group_name))

    return wanted_instances


def get_spaces_starting_with(arguments: Arguments) -> List[tuple]:
    wanted_instances = []
    for space in spaces.getSpaces():
        if not space["name"].startswith(arguments.starting_with):
            continue

        wanted_instances.append((InstanceType.space, space["spaceId"], space["name"]))

    return wanted_instances


def get_requested_instances_from_oneprovider(arguments: Arguments) -> List[tuple]:
    wanted_instances = []

    if arguments.tokens:  # invite tokens
        wanted_instances += get_tokens_starting_with(arguments)

    if arguments.groups:  # groups
        if arguments.spaces:
            wanted_instances += get_only_groups_under_spaces_starting_with(arguments)
        else:
            wanted_instances += get_all_users_groups_starting_with(arguments)

    if arguments.spaces:  # spaces
        wanted_instances += get_spaces_starting_with(arguments)

    if arguments.storages:  # storages
        wanted_instances += get_storages_starting_with(arguments)

    return wanted_instances


def get_requested_instances(arguments: Arguments) -> List[tuple]:
    if arguments.provider:
        return get_requested_instances_from_onezone(arguments)

    return get_requested_instances_from_oneprovider(arguments)


def print_instances(instances: List[tuple]) -> None:
    if len(instances) == 0:
        print("No instances to delete")
        exit(0)

    spaces_count = 0
    storages_count = 0
    tokens_count = 0
    groups_count = 0
    for instance_type, instance_id, instance_name in instances:
        if instance_type == InstanceType.space or instance_type == InstanceType.space_oz:
            instance_type = "Space"
            spaces_count += 1

        if instance_type == InstanceType.storage:
            instance_type = "Storage"
            storages_count += 1

        if instance_type == InstanceType.token:
            instance_type = "Token"
            tokens_count += 1

        if instance_type == InstanceType.group:
            instance_type = "Group"
            groups_count += 1

        print(f"{instance_type}: {instance_name}, id: {instance_id}")

    print(f"Spaces: \t{spaces_count}\nStorages: \t{storages_count}\nTokens: \t{tokens_count}\nGroups: \t{groups_count}")


def remove(args: argparse.Namespace) -> None:
    """
    Delete all instances of a given characteristics.
    """
    print("Starting processing for removal")
    arguments = process_args(args)
    instances = get_requested_instances(arguments)
    print_instances(instances)
    print_safety_notice("All this spaces, groups, tokens and storages will be deleted.")
    # if this program continues, it means, that user typed yes

    for instance_type, instance_id, instance_name in instances:
        if instance_type == InstanceType.space:
            spaces.removeSpace(instance_id)
            instance_type = "Space"

        if instance_type == InstanceType.space_oz:
            spaces.removeSpace(instance_id)
            instance_type = "Space"

        if instance_type == InstanceType.storage:
            time.sleep(1)  # sometimes storage need to be propagated
            storages.removeStorage(instance_id)
            instance_type = "Storage"

        if instance_type == InstanceType.token:
            tokens.deleteNamedToken(instance_id)
            instance_type = "Token"

        if instance_type == InstanceType.group:
            groups.removeGroup(instance_id)
            instance_type = "Group"

        print(f"{instance_type} {instance_name} with id {instance_id} deleted.")
        time.sleep(0.5)


def change_posix_permissions(arguments: Arguments, posix_permissions: int) -> None:
    posix_permissions = posix_permissions[-3:]
    try:
        int(posix_permissions, 8)
    except Exception as e:
        print(f"Error, posix permissions not in right format, error message: {e}")
        return

    instances = get_spaces_starting_with(arguments)
    print_instances(instances)
    print_safety_notice(f"POSIX permissions will be changed recursively to {posix_permissions} to these spaces.")

    for instance_type, instance_id, instance_name in instances:
        spaces.set_space_posix_permissions_recursive(instance_id, posix_permissions)
        print(f"Changed POSIX permissions of space {instance_name} with id {instance_id} to {posix_permissions}")


def change_directory_statistics(arguments: Arguments, status: str) -> None:
    change_to = True
    if status.lower() == "off":
        change_to = False
    instances = get_spaces_starting_with(arguments)
    print_instances(instances)
    print_safety_notice(f"Directory statistics status will be changed to '{status}' to these spaces.")

    for instance_type, instance_id, instance_name in instances:
        for oneprovider_index in range(len(Settings.get().ONEPROVIDERS_API_URL)):  # for all oneproviders
            spaces.change_directory_statistics(instance_id, change_to, oneprovider_index=oneprovider_index)
        print(f"Changed directory statistics status of space {instance_name} with id {instance_id} to {status}.")


def change(args: argparse.Namespace) -> None:
    """
    Changes all instances of given characteristics
    """
    print("Starting processing for change")
    arguments = process_args(args)

    if args.posix_permissions:
        change_posix_permissions(arguments, args.posix_permissions)
        return

    if args.directory_statistics:
        change_directory_statistics(arguments, args.directory_statistics)
        return


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
    if "build" not in oneprovider.get_configuration(oneprovider_index):
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

    # testing connection to email server
    result += mail.test_connection()

    if result == 0:
        Logger.log(3, "Onezone, Oneprovider, DAREG and email, if enabled, exist and respond.")
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

    workflow.register_space(os.path.join(base_path, directory))
