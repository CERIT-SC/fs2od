import os
from pprint import pprint
import json
import yaml
import filesystem
from settings import Settings
from utils import Logger
import spaces, files, request
from builtin import json_extender  # due to ability to convert date and datetime


def _set_file_json_metadata(file_id: str, data: dict):
    Logger.log(4, f"_set_file_json_metadata({file_id}, {data}):")
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/set_json_metadata
    if not data:
        Logger.log(2, f"No data given to _set_file_json_metadata (file ID {file_id})")

    url = "oneprovider/data/" + file_id + "/metadata/json"
    headers = dict({"Content-type": "application/json"})
    response = request.put(url, headers=headers, data=json.dumps(data, cls=json_extender.JSONEncoder))
    return response


def set_space_metadata_from_yaml(directory: os.DirEntry) -> bool:
    Logger.log(4, f"set_space_metadata_from_yaml({directory.path}):")

    yml_file = filesystem.get_trigger_metadata_file(directory)
    yml_content = filesystem.load_yaml(yml_file)

    if yml_content is None:
        # no need for log, already done
        return False

    space_id = filesystem.yamlContainsSpaceId(yml_content)
    if not space_id:
        Logger.log(3, f"File '{yml_file}' does not contain space_id")
        return False

    space_info = spaces.get_space(space_id)
    if "fileId" not in space_info or not space_info["fileId"]:
        Logger.log(3, f"Cannot get information for space with ID {space_id}")
        return False
    file_id = space_info["fileId"]

    return _set_file_json_metadata(file_id, yml_content).ok
