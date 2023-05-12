import json
import re
import time
from pprint import pprint
from settings import Settings
from utils import Logger
import storages, spaces, metadata, tokens, filesystem, groups, shares, files, transfers, request, workflow, dareg, onezone


def remove_spaces_of_provider(hostname_or_id: str, when_only_one_provider: bool = True):
    Logger.log(3, f"remove_spaces_of_provider(host_od_id={hostname_or_id},only_one_provider={when_only_one_provider})")
    provider_id = onezone.resolve_provider_id_from_id_or_hostname(hostname_or_id)

    if not provider_id:
        Logger.log(1, f"Provider with hostname or id {hostname_or_id} not found")
        return

    provider_spaces = onezone.get_providers_supported_spaces_from_onezone(provider_id)

    available_spaces = []
    for provider_space_id in provider_spaces:
        space_details = spaces.get_space_from_onezone(provider_space_id)
        if not space_details:
            continue
            
        if when_only_one_provider and len(space_details["providers"]) > 1:
            continue

        available_spaces.append((provider_space_id, space_details["name"]))

    if len(available_spaces) == 0:
        Logger.log(2, "No spaces to delete")
        return

    print("Next spaces will be deleted: ")
    for _, space_name in available_spaces:
        print(space_name)
    yes_no = input("Write yes to confirm and continue: ")

    if yes_no != "yes":
        print("Deletion was not confirmed, not continuing")

    Logger.log(3, f"All spaces of provider with id {hostname_or_id} will be deleted")

    for space_id, _ in available_spaces:
        spaces.removeSpace(space_id)



def sandbox(args):
    """
    Sandbox method where specific workflows (experiments, tests, ...) can be done.
    """
    var1 = args.var1
    var2 = args.var2
    var3 = args.var3
    Logger.log(3, "Run sandbox with variables:\nvar1=%s, var2=%s, var3=%s" % (var1, var2, var3))

    # a specific workflow can be defined here
    print(tokens.tokenExists(var1))
    # tokens.createInviteTokenToGroup(token_name=var1, group_id=var2)

    if var1 == "remove_spaces_of_provider":
        if not var2:
            Logger.log(1, "Provider id or hostname not provided")
            return
        remove_spaces_of_provider(var2, not bool(var3))
