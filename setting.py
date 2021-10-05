import yaml
import os
from pprint import pprint

# Loading configuration from YAML file
config_file = "config.yaml"
if os.path.exists(config_file):
    with open(config_file, 'r') as stream:
        CONFIG = yaml.safe_load(stream)
else:
    print("File", config_file, "doesn't exists.")

# HACK - disable warnings when curl can't verify the remote server by its certificate. Fix before production.
import urllib3
urllib3.disable_warnings()

## Allow output and debug prints
# 0 - silent mode, only errors are printed
# 1 - print base info, errors and warning are printed
# 2 - print detailed info, errors, warning and functions calls are printed
# 3 - print detailed info like previous, processed data values are also printed
DEBUG = 1

## TODO - Allow test mode
# All instances (spaces, tokens, groups, ...) are created with test prefix.
# These instances can be deleted by method test.deleteAllTestInstances(TEST_PREFIX)
TEST = True
TEST_PREFIX = "testTS_"

# Setup the access Onedata variables
ONEZONE_HOST = CONFIG['onezone']['host']
ONEZONE_API_KEY = CONFIG['onezone']['apiToken']

ONEPROVIDER_HOST = CONFIG['oneprovider']['host']
ONEPROVIDER_API_KEY = CONFIG['oneprovider']['apiToken']

ONEPANEL_HOST = CONFIG['onepanel']['host']
ONEPANEL_API_KEY = CONFIG['onepanel']['apiToken']

ONEZONE_API_URL = ONEZONE_HOST + "/api/v3/"
ONEPROVIDER_API_URL = ONEPROVIDER_HOST + "/api/v3/"
ONEPANEL_API_URL = ONEPANEL_HOST + "/api/v3/"

ONEZONE_AUTH_HEADERS = {'x-auth-token' : ONEZONE_API_KEY}
ONEPROVIDER_AUTH_HEADERS = {'x-auth-token' : ONEPROVIDER_API_KEY}
ONEPANEL_AUTH_HEADERS = {'x-auth-token' : ONEPANEL_API_KEY}
