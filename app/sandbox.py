import json
import re
import time
from pprint import pprint
from settings import Settings
from utils import Logger
import storages, spaces, metadata, tokens, filesystem, groups, shares, files, transfers, request, workflow

def sandbox(args):
    """ 
    Sandbox method where specific workflows (experiments, tests, ...) can be done.
    """
    var1 = args.var1
    var2 = args.var2
    var3 = args.var2
    print("Run sandbox with variables:")
    print("var1=%s, var2=%s, var3=%s" % (var1, var2, var3))
    print("***")

    # a specific workflow can be defined here
