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
