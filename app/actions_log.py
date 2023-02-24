import sys
from typing import Union, List

import requests


class Object:
    def __init__(self, object_type: str, object_name: str):
        self.type = object_type
        self.name = object_name
        self.id = ""

    def assign_id(self, object_id: str):
        self.id = object_id


def create_object(object_type: str, object_name: str) -> Object:
    return Object(object_type, object_name)


class ActionsLogger:
    __instance = None

    def __int__(self):
        if ActionsLogger.__instance is not None:
            raise Exception(
                "This class is a singleton! Created once, otherwise use ActionsLogger.get()"
            )
        else:
            self.log: List[Object] = []
            ActionsLogger.__instance = self

    @staticmethod
    def get():
        """
        Static access method, return instance of Settings or instantiate it.
        """
        if ActionsLogger.__instance is None:
            ActionsLogger()
        return ActionsLogger.__instance

    def log_pre(self, object_type: str, name: str):
        self.log.append(create_object(object_type, name))

    def log_post(self, obtained_id: Union[str, dict, bool]):
        if not obtained_id:
            self.rollback()
            sys.exit(1)

        last_object = self.log[-1]

        if last_object.type == "token":
            obtained_id = obtained_id["tokenId"]

        if last_object.type == "group_to_space":
            # only checking if returned right response, if not, doing rollback
            self.log.pop(-1)
            return

        if last_object.type == "auto_storage_import":
            # only checking if returned right response, if not, doing rollback
            self.log.pop(-1)
            return

        if last_object.type == "file_id":
            # only checking if returned right response, if not, doing rollback
            self.log.pop(-1)
            return

        last_object.assign_id(obtained_id)

    def print_actions_log(self):
        print(self.log)

    def rollback(self):
        pass


def get_actions_logger() -> ActionsLogger:
    return ActionsLogger.get()
