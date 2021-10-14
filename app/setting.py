import os
import sys
from pprint import pprint
import ruamel.yaml

# Loading configuration from YAML file
config_file = "./config.yaml"
if os.path.exists(config_file):
    with open(config_file, 'r') as stream:
        #CONFIG = yaml.safe_load(stream) # pyyaml
        yaml = ruamel.yaml.YAML(typ='safe')
        CONFIG = yaml.load(stream)
        
else:
    print("File", config_file, "doesn't exists.")
    sys.exit(-1)

# HACK - disable warnings when curl can't verify the remote server by its certificate. Fix before production.
import urllib3
urllib3.disable_warnings()

# Set debug and test mode
DEBUG = CONFIG['debug']
TEST = CONFIG['testMode']
TEST_PREFIX = CONFIG['testModePrefix']

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
