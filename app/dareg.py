import json
import requests

from utils import Logger
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
        "invite_token": invite_token,
        "public_URL": public_URL,
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    response_print(response)


def update_dataset(space_id, invite_token=None, public_URL=None):
    """
    Update the dataset.
    """
    url = Settings.get().config["dareg"]["host"] + "/datasets/" + space_id + "/"
    headers = {
        "Authorization": "Token " + Settings.get().config["dareg"]["token"],
        "Content-type": "application/json",
    }
    data = dict()
    if invite_token:
        data["invite_token"] = invite_token
    if public_URL:
        data["public_URL"] = public_URL

    response = requests.patch(url, headers=headers, data=json.dumps(data))
    response_print(response)


def log(space_id, type, message):
    """
    Log a record to dataset.
    """

    # TODO: Patch: not checking if dareg enabled
    if not Settings.get().DAREG_ENABLED:
        return

    url = Settings.get().config["dareg"]["host"] + "/logs/"
    headers = {
        "Authorization": "Token " + Settings.get().config["dareg"]["token"],
        "Content-type": "application/json",
    }
    data = {
        "dataset": Settings.get().config["dareg"]["host"] + "/datasets/" + space_id + "/",
        "type": type,
        "message": message,
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    response_print(response)


def get_index() -> bytes:
    # TODO: change to get congig, something in json
    """
    Get index only for checking if online.
    """
    url = Settings.get().config["dareg"]["host"]
    response = requests.get(url)
    Logger.log(5, response.text)

    response_print(response)

    return response.content
