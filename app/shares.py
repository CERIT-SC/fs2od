import json
import os
import time
from typing import Union, Tuple
from string import Template
import filesystem
import spaces
from settings import Settings
from utils import Logger, Utils
import request


GET_SHARE_TRIES = 10


def createShare(name, file_id, description=""):
    Logger.log(4, "createShare(%s, %s, description)" % (name, file_id))
    Logger.log(5, "description: %s" % description)

    if len(name) < Settings.get().MIN_ONEDATA_NAME_LENGTH:
        Logger.log(1, "Too short share name %s." % name)
        return

    name = Utils.clearOnedataName(name)

    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/create_share
    url = "oneprovider/shares"
    data = {"name": name, "description": description, "fileId": file_id}
    headers = dict({"Content-type": "application/json"})
    response = request.post(url, headers=headers, data=json.dumps(data))
    return response.json()["shareId"]


def getShare(share_id) -> dict:
    Logger.log(4, "getShare(%s):" % share_id)
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/get_share
    url = "oneprovider/shares/" + share_id
    response = request.get(url)

    if not response.ok:
        return {}

    return response.json()


def createAndGetShare(name, file_id, description=""):
    share_id = createShare(name, file_id, description)
    time.sleep(2 * Settings.get().config["sleepFactor"])
    return getShare(share_id)


def updateShare(shid, name=None, description=None):
    Logger.log(4, "updateShare(%s, %s, description)" % (shid, name))
    Logger.log(5, "description: %s" % description)
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/update_share
    url = "oneprovider/shares/" + shid
    data = dict()
    if name is not None:
        data["name"] = name
    if description is not None:
        data["description"] = description
    if data:
        headers = dict({"Content-type": "application/json"})
        response = request.patch(url, headers=headers, data=json.dumps(data))

        if response.ok:
            Logger.log(5, f"share with id {shid} was")
        else:
            Logger.log(5, f"share with id {shid} could not be updated")

        return response
    else:
        Logger.log(3, f"no content to update the share {shid}")


def get_share_starting_with(space_id: str, text: str) -> str:
    Logger.log(4, f"get_share_starting_with(sid={space_id},share_name={text})")

    shares = spaces.get_space_shares(space_id)
    if not shares:
        return ""

    for share_id in shares:
        share_info = getShare(share_id)
        if "name" not in share_info:
            continue

        share_name: str = share_info["name"]
        if share_name.startswith(text):
            return share_id

    return ""


def create_share_description(directory: Union[os.DirEntry, str], ignore_config_parse_metadata: bool = False) \
        -> Tuple[str, str]:
    Logger.log(4, f"create_share_description({directory})")
    if type(directory) != os.DirEntry:
        # hack to get DirEntry
        directory = filesystem.get_dir_entry_of_directory(directory)

    if directory is None:
        return ""

    yaml_file = filesystem.getMetaDataFile(directory)
    if not yaml_file:
        return ""

    yaml_contents = filesystem.loadYaml(yaml_file)
    if not yaml_contents:
        return ""

    space_id = filesystem.yamlContainsSpaceId(yaml_contents)
    if not space_id:
        return ""

    space_info = spaces.get_space(space_id)
    if not space_info:
        return ""

    space_name = space_info.get("name", "")

    shares = []
    for try_number in range(GET_SHARE_TRIES):
        Logger.log(3, f"Getting shares of space with id {space_id} and name {space_name} "
                      f"try: {try_number + 1}/{GET_SHARE_TRIES}")
        shares = spaces.get_space_shares(space_id)
        if shares:
            break

        time.sleep(Settings.get().config["sleepFactor"] * 2)

    if not shares:
        return ""

    # TODO: care better of right share id
    share_id = shares[0]
    share_info = getShare(share_id)
    if not share_info:
        return ""

    share_file_id = share_info.get("rootFileId", "")

    if Settings.get().config["metadataFileTags"]["onedata"] in yaml_contents:
        yaml_contents.pop(Settings.get().config["metadataFileTags"]["onedata"])

    if Settings.get().config["metadataFileTags"]["inviteToken"] in yaml_contents:
        yaml_contents.pop(Settings.get().config["metadataFileTags"]["inviteToken"])

    if Settings.get().config["metadataFileTags"]["space"] in yaml_contents:
        yaml_contents.pop(Settings.get().config["metadataFileTags"]["space"])

    metadata_section = ""
    yaml_string = ""

    if Settings.get().config["parseMetadataToShare"] and not ignore_config_parse_metadata:
        yaml_string = filesystem.convert_dict_to_yaml(yaml_contents)

    # if we do not have anything to write, we will not
    if yaml_string and yaml_contents:
        metadata_section = f"""## Metadata file
Here is the actual copy of metadata file:
```yaml
{yaml_string}
```
        """

    to_substitute = {
        "dataset_name": space_name,
        "institution_name": Settings.get().config["institutionName"],
        "share_file_id": share_file_id,
        "metadata_section": metadata_section
    }
    template = filesystem.load_file_contents("share_description_base.md")
    src = Template("".join(template))
    result = src.substitute(to_substitute)

    return result, share_id
