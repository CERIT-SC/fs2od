import time
from io import TextIOWrapper
import os.path
from typing import Union, List, Optional, Tuple
from utils import Logger, Utils, Settings
import test
import actions_rollback

ACTION_LOG_FILE = "actions_log.latest.log"
ACTION_SEQUENCE_RENAMING_TRIES = 10


class Action:
    def __init__(self, object_type: str, object_name: str):
        self.type = object_type
        self.name = object_name
        self.id = ""

    def __str__(self):
        return f"<action_logs.Action object, type={self.type}, name={self.name}>"

    def assign_id(self, object_id: str):
        self.id = object_id


def create_object(object_type: str, object_name: str) -> Action:
    return Action(object_type, object_name)


class ActionsLogger:
    __instance = None

    def __init__(self):
        if ActionsLogger.__instance is not None:
            raise Exception(
                "This class is a singleton! Created once, otherwise use ActionsLogger.get()"
            )
        else:
            self.log: List[Action] = []
            self.file: Optional[TextIOWrapper] = None
            ActionsLogger.__instance = self

    @staticmethod
    def get():
        """
        Static access method, return instance of Settings or instantiate it.
        """
        if ActionsLogger.__instance is None:
            ActionsLogger()
        return ActionsLogger.__instance

    def new_actions_log(self):
        """
        Starts new actions log for new actions sequence. If something not went successfully before, rollbacks
        """
        Logger.log(4, "starting new actions log")
        # if we have something in actions log, it means, that last action was not successful
        # so first we must rollback()
        if self.file:  # we have the file still opened
            # no need to do rollback here, because it will close and stay on filesystem
            self.close_file()
        if len(self.log) != 0 or os.path.isfile(ACTION_LOG_FILE):
            Logger.log(1, "found old actions log, rolling back")
            self.rollback()

        # buffering=1 means, it will flush the file after each line
        self.file = open(ACTION_LOG_FILE, "w+", encoding="utf-8", buffering=1)

    def log_pre(self, object_type: str, name: str):
        """
        Appends to ActionsLogger log before action was run
        """
        self.log.append(create_object(object_type, name))
        self.file.write(f"{object_type},{name},")
        self.file.flush()

    def log_post(self, obtained_id: Union[str, dict, bool], only_check=False) -> bool:
        """
        After action run, appends obtained id to log
        Returns False when rollback was run, otherwise True
        """

        now_testing = self.log[-1].type

        if only_check:
            self.log.pop(-1)

        if not obtained_id:
            Logger.log(1, f"Did not get id for {now_testing}. Doing rollback.")
            self.rollback(include_file=False)
            return False

        if only_check:
            self.file.write(f"only_check\n")
            return True

        last_object = self.log[-1]

        if last_object.type == "token":
            obtained_id = obtained_id["tokenId"]

        last_object.assign_id(obtained_id)

        self.file.write(f"{obtained_id}\n")
        return True

    def close_file(self):
        if type(self.file) == TextIOWrapper:
            self.file.close()
            self.file = None

    def finish_actions_log(self):
        """
        Stops logging for actual actions sequence. Removing log list and log file.
        """
        self.close_file()
        Logger.log(4, "actions log finished, removing file")

        self.log = []
        if os.path.isfile(ACTION_LOG_FILE):
            os.remove(ACTION_LOG_FILE)
            Logger.log(4, "actions log finished, removed file")

    def print_actions_log(self):
        for action in self.log:
            print(action)

    @staticmethod
    def build_list_sequence(log_list: List[Action]) -> dict:
        """
        Builds sequence from ActionsLogger list (reverse order) to sequence dictionary (normal order)
        """
        sequence = {"queue": []}

        log_list = log_list[::-1]  # reversing list

        for item in log_list:
            sequence[item.type] = (item.name, item.id)
            sequence["queue"].append(item.type)

        return sequence

    @staticmethod
    def build_file_sequence(log_file_name: str) -> dict:
        """
        Builds sequence from file created by ActionsLogger (reverse order) to sequence dictionary (normal order)
        """
        with open(log_file_name, "r", encoding="UTF-8") as file:
            items = file.readlines()

        sequence = {"queue": []}

        for item in items:
            item = item.strip()
            item_list = item.split(",")

            if len(item_list) < 2:  # error on the line or blank
                continue

            item_type = item_list[0]
            item_name = item_list[1]

            # this is then the last line, on which failed
            if len(item_list) == 2:
                # means it have name, so keep
                if item_name:
                    sequence[item_type] = (item_name, None)
                    sequence["queue"].append(item_type)
                    continue

            item_id = item_list[2]
            # not needed, not reversible
            if item_id == "only_check":
                continue
            sequence[item_type] = (item_name, item_id)
            sequence["queue"].append(item_type)

        sequence["queue"] = sequence["queue"][::-1]  # reversing list

        return sequence

    @staticmethod
    def merge_sequences(sequence_1: dict, sequence_2: dict) -> dict:
        """
        Merges two sequences (type does not matter). If sequences are the same, returns merged sequence
        otherwise returns empty dict.
        Two sequences are same when they have same queue and first ids to rollback.
        """
        queue_1 = sequence_1["queue"]
        queue_2 = sequence_2["queue"]

        if not queue_1 or not queue_2:
            return {}

        # different runs, different sequences
        if queue_1[0] != queue_2[0]:
            return {}

        # common first command but another names and/or ids
        if sequence_1[queue_1[0]] != sequence_2[queue_2[0]]:
            return {}

        final_queue = queue_1.copy() if len(queue_1) > len(queue_2) else queue_2.copy()
        sequence_1.update(sequence_2)
        sequence_1["queue"] = final_queue

        return sequence_1

    def build_sequence(self, include_file: bool = True) -> Union[Tuple[dict, dict], dict]:
        """
        Builds sequence how to approach rollback in right direction.
        There are be 3 possibilities:
        - log from list
        - log from file
        - log from both, list and file
        Computes what to do in any of cases.
        If log from file not wanted, include_file should be set to False
        Returns sequence dict, or two sequences dict in tuple
        """
        log_sequence = {"queue": []}
        file_sequence = {"queue":[]}

        if self.log:
            log_sequence = self.build_list_sequence(self.log)

        if not include_file:
            return log_sequence

        if os.path.isfile(ACTION_LOG_FILE):
            file_sequence = self.build_file_sequence(ACTION_LOG_FILE)

        final_sequence = self.merge_sequences(log_sequence, file_sequence)

        if not final_sequence:
            return log_sequence, file_sequence

        return final_sequence

    @staticmethod
    def serialize_sequence(sequence: dict) -> str:
        """
        Serializes sequence to log-file-like string
        """
        sequence_queue = sequence["queue"]
        sequence_queue = sequence_queue[::-1]

        serialized_out = ""

        for action_type in sequence_queue:
            action_name = sequence[action_type][0]
            action_id = sequence[action_type][1]
            serialized_out += f"{action_type},{action_name},{action_id}\n"

        return serialized_out

    @staticmethod
    def write_sequence_to_file(sequence: dict) -> bool:
        """
        Writes unsuccessfully provided rollback sequence to file.
        Filename should be ``rollback.sequence``. If this name already used, saves file to ``rollback_XXXX.sequence``
        where XXXX are four random characters.
        """
        serialized_out = ActionsLogger.serialize_sequence(sequence)

        filename = "rollback.sequence"
        for try_number in range(ACTION_SEQUENCE_RENAMING_TRIES):
            if not os.path.isfile(filename):
                with open(filename, "w+", encoding="utf-8") as file:
                    file.write(serialized_out)
                return True

            filename = "rollback_" + Utils.create_uuid(4) + ".sequence"

        return False

    @staticmethod
    def move_storage_deleting_after_space(sequence: dict) -> dict:
        queue: list = sequence["queue"]

        if "storage" not in queue or "space" not in queue:
            return sequence

        storage_index = queue.index("storage")
        space_index = queue.index("space")

        queue.pop(storage_index)
        queue.insert(space_index, "storage")

        sequence["queue"] = queue

        return sequence

    @staticmethod
    def rollback_actions(sequence: dict) -> bool:
        """
        Provides real rollback. Testing connection at the beginning. If connected successfully, does rollback.
        Returns True if everything done, otherwise False
        """
        if not sequence:
            return True

        sequence = ActionsLogger.move_storage_deleting_after_space(sequence)

        # at the beginning we must test the connection
        Logger.log(3, "rollback - testing connection")
        connection_status = test.testConnection()
        # means if something not connected
        if connection_status != 0:
            Logger.log(3, "rollback - connection failed, writing to file")
            ActionsLogger.write_sequence_to_file(sequence)
            return False

        success = True
        sequence_queue = sequence["queue"]

        for action in sequence_queue:
            if action == "token":
                success = actions_rollback.action_token(sequence[action][0], sequence[action][1]) and success
            elif action == "group":
                success = actions_rollback.action_group(sequence[action][0], sequence[action][1]) and success
            elif action == "storage":
                success = actions_rollback.action_storage(sequence[action][0], sequence[action][1]) and success
            elif action == "space":
                success = actions_rollback.action_space(sequence[action][0], sequence[action][1]) and success

        if not success:
            Logger.log(1, "rollback - rollback was not completed successfully, need to check logs")
            return success

        Logger.log(3, "rollback - rollback was successful")
        return success

    def rollback(self, include_file: bool = True) -> None:
        """
        First signal to do rollback. Creates sequences and runs them
        If include_file is False, log from file will be skipped
        """
        Logger.log(2, "starting rollback")
        time.sleep(5 * Settings.get().config["sleepFactor"])
        self.close_file()

        sequence_1 = self.build_sequence(include_file)

        if type(sequence_1) == tuple:
            sequence_2 = sequence_1[1]
            self.rollback_actions(sequence_2)
            sequence_1 = sequence_1[0]

        self.rollback_actions(sequence_1)

        self.finish_actions_log()
        Logger.log(2, "rollback finished")


def get_actions_logger() -> ActionsLogger:
    return ActionsLogger.get()
