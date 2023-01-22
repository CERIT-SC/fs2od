import json
import requests
from settings import Settings
from request import response_print, debug_print


def register_dataset(space_id, name, path, invite_token=None, public_URL=None):
    """
    Register a dataset to datasets register.
    """
    url = Settings.get().config["dareg"]["host"] + "/datasets/"
    headers = {
        "Authorization": "Token " + Settings.get().config["dareg"]["token"],
        "Content-type": "application/json",
    }
    data = {
        "origin_instance": Settings.get().config["dareg"]["host"]
        + "/instances/"
        + str(Settings.get().config["dareg"]["origin_instance_pk"])
        + "/",
        "name": name,
        "path": path,
        "space_id": space_id,
        "public_URL": public_URL,
        "invite_token": invite_token,
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    response_print(response)
    debug_print(response)
