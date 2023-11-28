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
    for token_id in tokens.list_all_named_tokens():
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
        group_name = groups.get_group_details(group_id)["name"]
        if not group_name.startswith(arguments.starting_with):
            continue

        wanted_instances.append((InstanceType.group, group_id, group_name))

    return wanted_instances


def get_only_groups_under_spaces_starting_with(arguments: Arguments) -> List[tuple]:
    wanted_instances = []
    for space in spaces.get_all_user_spaces():
        if "spaceId" not in space:
            Logger.log(4, "Space has no element spaceId. Skipping")
            continue

        space_groups = spaces.list_space_groups_ids(space["spaceId"])
        for group_id in space_groups:
            group_info = groups.get_group_details(group_id)

            if "name" not in group_info:
                Logger.log(4, "Group has no element name. Skipping.")
                continue

            group_name = group_info["name"]
            if not group_name.startswith(arguments.starting_with):
                continue

            wanted_instances.append((InstanceType.group, group_id, group_name))

    return wanted_instances


def get_zone_spaces_starting_with(arguments: Arguments) -> List[tuple]:
    wanted_instances = []
    for space in spaces.get_all_user_spaces():
        if not space["name"].startswith(arguments.starting_with):
            continue

        wanted_instances.append((InstanceType.space, space["spaceId"], space["name"]))

    return wanted_instances


def get_provider_spaces_starting_with(arguments: Arguments, provider_index: int) -> List[tuple]:
    wanted_instances = []
    for space_id, space_name in spaces.get_all_provider_spaces_with_names(provider_index).items():
        if not space_name.startswith(arguments.starting_with):
            continue

        wanted_instances.append((InstanceType.space, space_id, space_name))

    return wanted_instances


def get_requested_instances_from_oneprovider(arguments: Arguments) -> List[tuple]:
    wanted_instances = []

    if arguments.tokens:  # invite tokens
        wanted_instances += get_tokens_starting_with(arguments)

    if arguments.groups:  # groups
        if arguments.spaces:
            requested_groups = get_only_groups_under_spaces_starting_with(arguments)

            if not requested_groups:
                requested_groups = get_all_users_groups_starting_with(arguments)

            wanted_instances += requested_groups

        else:
            wanted_instances += get_all_users_groups_starting_with(arguments)

    if arguments.spaces:  # spaces
        wanted_instances += get_zone_spaces_starting_with(arguments)

    if arguments.storages:  # storages
        wanted_instances += get_storages_starting_with(arguments)

    return wanted_instances


def get_requested_instances(arguments: Arguments) -> List[tuple]:
    if arguments.provider:
        return get_requested_instances_from_onezone(arguments)

    return get_requested_instances_from_oneprovider(arguments)


def print_instances(instances: List[tuple]) -> None:
    if len(instances) == 0:
        print("No instances matching rules found")
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
    error_messages = []

    for instance_type, instance_id, instance_name in instances:
        is_ok = False
        if instance_type == InstanceType.space:
            is_ok = spaces.removeSpace(instance_id).ok
            instance_type = "Space"

        if instance_type == InstanceType.space_oz:
            is_ok = spaces.removeSpace(instance_id).ok
            instance_type = "Space"

        if instance_type == InstanceType.storage:
            time.sleep(1)  # sometimes storage need to be propagated
            is_ok = storages.removeStorage(instance_id).ok
            instance_type = "Storage"

        if instance_type == InstanceType.token:
            is_ok = tokens.deleteNamedToken(instance_id).ok
            instance_type = "Token"

        if instance_type == InstanceType.group:
            is_ok = groups.removeGroup(instance_id).ok
            instance_type = "Group"

        if is_ok:
            print(f"{instance_type} {instance_name} with id {instance_id} deleted.")
        else:
            error_messages.append(f"Error: {instance_type} {instance_name} with id {instance_id} could not be deleted.")

        time.sleep(0.5)

    for error_message in error_messages:
        print(error_message)


def change_posix_permissions(arguments: Arguments, posix_permissions: int) -> None:
    posix_permissions = posix_permissions[-3:]
    try:
        int(posix_permissions, 8)
    except Exception as e:
        print(f"Error, posix permissions not in right format, error message: {e}")
        return

    instances = get_zone_spaces_starting_with(arguments)
    print_instances(instances)
    print_safety_notice(f"POSIX permissions will be changed recursively to {posix_permissions} to these spaces.")

    for instance_type, instance_id, instance_name in instances:
        status = spaces.set_space_posix_permissions_recursive(instance_id, posix_permissions)
        if not status:
            print(f"Change of POSIX permissions of space {instance_name} with id {instance_id} failed, "
                  f"space does not belong to primary Oneprovider")

        print(f"Changed POSIX permissions of space {instance_name} with id {instance_id} to {posix_permissions}")


def change_directory_statistics(arguments: Arguments, status: str) -> None:
    change_to = True
    if status.lower() == "off":
        change_to = False
    instances = get_zone_spaces_starting_with(arguments)
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


def get_all_spaces_with_distribution(arguments: Arguments, used_providers: list) -> dict[str, dict[str, int, dict]]:
    """
    Returns dict of spaces with names and their distribution among providers
    """
    provider_spaces = {}

    for provider_index in used_providers:
        actual_spaces = get_provider_spaces_starting_with(arguments, provider_index)
        for _, space_id, space_name in actual_spaces:
            space_info = provider_spaces.get(space_id, {"name": space_name, "providers": []})
            space_info["providers"].append(provider_index)
            provider_spaces[space_id] = space_info

    return provider_spaces


def get_providers_index_id_map() -> list[str]:
    """
    Returns dict of providers with their index as key and id as value
    """
    providers = []
    for provider_index in range(len(Settings.get().ONEPROVIDERS_API_URL)):
        provider_id = oneprovider.get_provider_id(provider_index)
        providers.append(provider_id)

    return providers


def get_occupation_of_space_on_provider(space_id: str, provider_index: int, providers_map: list[str]) -> tuple[int, int]:
    """
    Returns dict of providers with their occupation on given space
    space_details = {
        "name": "space_name",
        "supportingProviders": {
            "provider_id":int support,
            "provider_id":int support
        },
        "spaceOccupancy":int occupancy,
        ...
    }
    """
    space_info = spaces.getSpaceDetails(space_id, provider_index)
    support_size = space_info["supportingProviders"][providers_map[provider_index]]
    space_occupancy = space_info["spaceOccupancy"]

    return support_size, space_occupancy


def append_occupation_information(spaces_list: dict, providers_map: list[str]):
    """
    Returns dict of spaces with names and their occupation information
    Final dict looks like this:
    spaces_list = {
        "space_id": {
            "name": "space_name",
            "providers": [int, int, ...],
            "occupancy": {
                provider_index: tuple(
                    "support": int,
                    "occupancy": int
                ),
                provider_index: tuple(
                    "support": int,
                    "occupancy": int
                ),
                ...
            }
            ...
        }
    """
    for space_id, space_info in spaces_list.items():
        spaces_list[space_id]["occupancy"] = {}
        space_providers = space_info["providers"]
        for provider_index in space_providers:
            occupancy = get_occupation_of_space_on_provider(space_id, provider_index, providers_map)
            spaces_list[space_id]["occupancy"][provider_index] = occupancy

    return spaces_list


def print_stats(spaces_list: dict, used_providers: list) -> None:
    total_provider_support = {provider_id: 0 for provider_id in used_providers}
    total_provider_occupancy = {provider_id: 0 for provider_id in used_providers}

    print("Statistics of spaces:")
    print("----------------------")
    print("Used providers:")
    for provider_index in used_providers:
        print(f"Provider index '{provider_index}': {Settings.get().ONEPROVIDERS_DOMAIN_NAMES[provider_index]}")
    print("----------------------")

    for space_id, space_info in spaces_list.items():
        space_name = space_info["name"]
        space_occupancy = space_info["occupancy"]
        space_total_support = 0
        space_total_occupancy = 0

        print(f"Space '{space_name}' with id '{space_id}':")
        for provider_index, provider_occupancy in space_occupancy.items():
            provider_support = provider_occupancy[0]
            provider_occupancy = provider_occupancy[1]
            total_provider_support[provider_index] += provider_support
            total_provider_occupancy[provider_index] += provider_occupancy
            space_total_support += provider_support
            space_total_occupancy += provider_occupancy
            print(f"\t'{provider_index}': support: {provider_support:,} bytes, "
                  f"occupancy: {provider_occupancy:,} bytes")
        print(f"\tTotal support: {space_total_support:,} bytes, total occupancy: {space_total_occupancy:,} bytes")

    print("----------------------")

    print("Support and occupancy by provider:")
    for provider_index in used_providers:
        print(f"Provider '{provider_index}': support: {total_provider_support[provider_index]:,} bytes, "
              f"occupancy: {total_provider_occupancy[provider_index]:,} bytes")
    print("")
    print("Total support and occupancy:")
    print(f"Support: {sum(total_provider_support.values()):,} bytes, occupancy: {sum(total_provider_occupancy.values()):,} bytes")


def separate_used_providers(arguments: Arguments, provider_map: list) -> list[int]:
    number_of_providers = len(Settings.get().ONEPROVIDERS_API_URL)

    provider_id = onezone.resolve_provider_id_from_id_or_hostname(arguments.provider)
    generator = range(number_of_providers)
    if provider_id and provider_id in provider_map:
        generator = [provider_map.index(provider_id)]

    return generator


def stats(args: argparse.Namespace) -> None:
    """
    Show stats of spaces with given rule
    """
    print("Starting processing for stats")
    args.with_more_providers = False
    arguments = process_args(args)

    provider_map = get_providers_index_id_map()
    used_providers = separate_used_providers(arguments, provider_map)
    spaces_list = get_all_spaces_with_distribution(arguments, used_providers)
    append_occupation_information(spaces_list, provider_map)

    print_stats(spaces_list, used_providers)


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
    if "error" in spaces.get_all_user_spaces():
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
