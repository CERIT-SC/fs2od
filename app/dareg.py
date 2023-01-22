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
        "invite_token": invite_token,
        "public_URL": public_URL,
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    response_print(response)
    debug_print(response)
    # return ID of the new dataset
    return response.json()["pk"]


def update_dataset(dareg_dataset_id, invite_token=None, public_URL=None):
    """
    Update the dataset.
    """
    url = Settings.get().config["dareg"]["host"] + "/datasets/" + str(dareg_dataset_id) + "/"
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
    debug_print(response)


def log(dareg_dataset_id, type, message):
    """
    Log a record to dataset.
    """
    url = Settings.get().config["dareg"]["host"] + "/logs/"
    headers = {
        "Authorization": "Token " + Settings.get().config["dareg"]["token"],
        "Content-type": "application/json",
    }
    data = {
        "dataset": Settings.get().config["dareg"]["host"]
        + "/datasets/"
        + str(dareg_dataset_id)
        + "/",
        "type": type,
        "message": message,
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    response_print(response)
    debug_print(response)
