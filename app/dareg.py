import json
import requests
from requests import request

from utils import Logger
from settings import Settings, DaregCreds
from request import response_print, debug_print

# TEMPORARY: duplication from Settings
class Dareg:
    def __init__(self, creds: DaregCreds):
        self.enabled: bool = creds.enabled
        self.host: str = creds.host
        self.token: str = creds.token
        self.project: str = creds.project

    # Temporary: attributes are passed separately
    # def register_dataset(self) -> bool:
    def register_dataset(self, space_name: str, description: str,
                         metadata: dict, file_id: str, share_id: str,
                         dataset_id: str) -> bool:
        """
        Registers a dataset to a new interface of DAREG
        """
        Logger.log(4, f"Dareg.register_dataset({space_name},file_id={file_id}, "
                      f"share_id={share_id}, dataset_id={dataset_id}, "
                      f"description=[redacted], metadata=[redacted])")
        if not self.enabled:
            return True

        body = {
            "name": space_name,
            "description": space_name,
            "metadata": "{}",
            "onedata_file_id": file_id,
            "onedata_share_id": share_id,
            "onedata_dataset_id": dataset_id,
            "project": self.project
        }
        auth = f"Token {self.token}"

        headers = {
            "Authorization": auth,
        }

        r = request(method="POST", url=self.host, data=body, headers=headers)
        # debug_print(r)
        Logger.log(5, "Response content:", pretty_print=r.content)


        rv = r.ok

        Logger.log(4, f"Dareg.register_dataset finished, returning {rv}")
        return rv


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
