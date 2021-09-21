import requests
from pprint import pprint

# HACK - disable warnings when curl can't verify the remote server by its certificate. Fix before production.
import urllib3
urllib3.disable_warnings()

DEBUG = False

# Setup the access Onedata variables
ONEZONE_HOST = "https://datahub.egi.eu"
ONEZONE_API_KEY_BCK = ""
ONEZONE_API_KEY = ""

ONEPROVIDER_HOST = "https://storage-ceitec1-fe1.ceitec.muni.cz"
ONEPROVIDER_API_KEY = ""

ONEPANEL_HOST="https://muni.datahub.egi.eu"
ONEPANEL_API_KEY = ""

ONEZONE_API_URL = ONEZONE_HOST + "/api/v3/"
ONEPROVIDER_API_URL = ONEPROVIDER_HOST + "/api/v3/"
ONEPANEL_API_URL = ONEPANEL_HOST + "/api/v3/"

#auth_headers = {'x-auth-token' : ONEZONE_API_KEY}

ONEZONE_AUTH_HEADERS = {'x-auth-token' : ONEZONE_API_KEY}
ONEPANEL_AUTH_HEADERS = {'x-auth-token' : ONEPANEL_API_KEY}

# User id - service identity
USER_ID = ""

# Group id of groups of administrators
GROUP_ID = ""