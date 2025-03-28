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
        self.schema: str = creds.schema

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
            "metadata": metadata,
            "onedata_file_id": file_id,
            "onedata_share_id": share_id,
            "onedata_dataset_id": dataset_id,
            "project": self.project,
            "schema": self.schema,
            "status": "new"
        }
        auth = f"Token {self.token}"

        headers = {
            "Authorization": auth,
        }

        r = request(method="POST", url=self.host + "datasets/shadow/", json=body, headers=headers)
        # debug_print(r)
        Logger.log(5, "Response content:", pretty_print=r.content)


        rv = r.ok

        Logger.log(4, f"Dareg.register_dataset finished, returning {rv}")
        return rv

    def get_index(self):
        """
        Get index only for checking if online.
        """
        Logger.log(4, "Dareg.get_index()")
        response = requests.get(self.host)
        Logger.log(5, response.text)

        response_print(response)

        return response.content
