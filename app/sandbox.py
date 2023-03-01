import json
import re
import time
from pprint import pprint
from settings import Settings
from utils import Logger
import storages, spaces, metadata, tokens, filesystem, groups, shares, files, transfers, request, workflow, dareg


def sandbox(args):
    """
    Sandbox method where specific workflows (experiments, tests, ...) can be done.
    """
    var1 = args.var1
    var2 = args.var2
    var3 = args.var3
    Logger.log(3, "Run sandbox with variables:\nvar1=%s, var2=%s, var3=%s" % (var1, var2, var3))

    # a specific workflow can be defined here

    #tokens.tokenExists(var1)

    def removeSpacesAndGroupsSupportedByProvider(provider_id):
        """
        Remove all spaces (with its groups) which are supported on a specified provider.
        """
        for space in spaces.getSpaces():
            space_id =space['spaceId']
            print("Processing space", space_id)
            get_space = spaces.getSpaceDetailsOnezone(space_id)
            providers = get_space['providers']
            if len(providers) == 1 and provider_id in providers:
                groups_list = spaces.listSpaceGroups(space_id)
                for gid in groups_list:
                    group_name = groups.getGroupDetails(gid)['name']
                    if group_name == get_space['name']:
                        print("Removing group %s (%s)" % (group_name, gid))
                print("Removing space %s (%s)" % (get_space['name'], space_id))
                #spaces.removeSpace(space_id)

    removeSpacesAndGroupsSupportedByProvider(var1)
