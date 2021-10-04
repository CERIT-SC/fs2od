import yaml
import os
import requests
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

DEBUG = False

# Setup the access Onedata variables
ONEZONE_HOST = "https://datahub.egi.eu"
ONEZONE_API_KEY_BCK = "MDAxY2xvY2F00aW9uIGRhdGFodWIuZWdpLmV1CjAwNmJpZGVudGlmaWVyIDIvbm1kL3Vzci004M2QwM2IwNWFiOGZkY2E3NDMwYjRmYTAxMDkzMzYzMGNoOGZkYy9hY3QvNmY4YjRjMjQ5ZTZkNjhjYzQ3ZDQ3ODhiYjFlMmE5ZTJjaDk4NWIKMDAxOWNpZCBpbnRlcmZhY2UgPSByZXN00CjAwMjRjaWQgc2VydmljZSA9IG96dy1vbmV6b25lfG9wdy00qCjAwMmZzaWduYXR1cmUgRnhJnVkMp7B4i45AYey7hKdY8n8NhPPEpITeu9x4wtwK"
ONEZONE_API_KEY = "MDAxY2xvY2F00aW9uIGRhdGFodWIuZWdpLmV1CjAwNmJpZGVudGlmaWVyIDIvbm1kL3Vzci004M2QwM2IwNWFiOGZkY2E3NDMwYjRmYTAxMDkzMzYzMGNoOGZkYy9hY3QvYzBlZjJmNTdhMmZlZDczOTAwNTViN2UzMzdmMmYwZjhjaDIxYzkKMDAxOWNpZCBpbnRlcmZhY2UgPSByZXN00CjAwMmFjaWQgc2VydmljZSA9IG96dy1vbmV6b25lfG9wdy00qfG9wcC00qCjAwMmZzaWduYXR1cmUgOjCpFUxZeC01d27az9I61HcddjvDCjqTQN02B5cnTHpE4K"

ONEPROVIDER_HOST = "https://muni.datahub.egi.eu"
ONEPROVIDER_API_KEY = "MDAxY2xvY2F00aW9uIGRhdGFodWIuZWdpLmV1CjAwNmJpZGVudGlmaWVyIDIvbm1kL3Vzci004M2QwM2IwNWFiOGZkY2E3NDMwYjRmYTAxMDkzMzYzMGNoOGZkYy9hY3QvYzBlZjJmNTdhMmZlZDczOTAwNTViN2UzMzdmMmYwZjhjaDIxYzkKMDAxOWNpZCBpbnRlcmZhY2UgPSByZXN00CjAwMmFjaWQgc2VydmljZSA9IG96dy1vbmV6b25lfG9wdy00qfG9wcC00qCjAwMmZzaWduYXR1cmUgOjCpFUxZeC01d27az9I61HcddjvDCjqTQN02B5cnTHpE4K"

ONEPANEL_HOST="https://muni.datahub.egi.eu"
ONEPANEL_API_KEY = "MDAxY2xvY2F00aW9uIGRhdGFodWIuZWdpLmV1CjAwNmJpZGVudGlmaWVyIDIvbm1kL3Vzci004M2QwM2IwNWFiOGZkY2E3NDMwYjRmYTAxMDkzMzYzMGNoOGZkYy9hY3QvY2E00MTQ3YjAzNjFmZDI00ZGU3YmYwZmIxZjhkMWMyODFjaDkwODcKMDAxOGNpZCBzZXJ2aWNlID00gb3BwLSoKMDAyZnNpZ25hdHVyZSB1yUQswsvu01KXY333hxlOvUfVPV1roTIxG7b9mOqSYUgo"

ONEZONE_API_URL = ONEZONE_HOST + "/api/v3/"
ONEPROVIDER_API_URL = ONEPROVIDER_HOST + "/api/v3/"
ONEPANEL_API_URL = ONEPANEL_HOST + "/api/v3/"

#auth_headers = {'x-auth-token' : ONEZONE_API_KEY}

ONEZONE_AUTH_HEADERS = {'x-auth-token' : ONEZONE_API_KEY}
ONEPANEL_AUTH_HEADERS = {'x-auth-token' : ONEPANEL_API_KEY}
