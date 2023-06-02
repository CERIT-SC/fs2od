from pprint import pprint
import json
import yaml
from settings import Settings
from utils import Logger
import spaces, files, request


def _setFileJsonMetadata(file_id, data):
    Logger.log(4, "_setFileJsonMetadata(%s, data):" % file_id)
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/set_json_metadata
    if not data:
        Logger.log(2, "No data given to setFileJsonMetadata (file ID %s)" % file_id)

    url = "oneprovider/data/" + file_id + "/metadata/json"
    headers = dict({"Content-type": "application/json"})
    response = request.put(url, headers=headers, data=json.dumps(data))
    return response


def _loadConfigYAML(space_id):
    """
    Load configuration YAML file from root directory of space and return its file_id and content.
    Return None as content if such metadatafile doesn't exist.
    """
    Logger.log(4, "_loadConfigYAML(%s):" % space_id)
    # get file_id of space dir
    space = spaces.get_space(space_id)
    file_id = space["fileId"]

    # find ymls
    space_content = files.listDirectory(file_id)
    for metadataFile in Settings.get().config["metadataFiles"]:
        list_yml_files = list(
            filter(lambda x: metadataFile in x["name"], space_content["children"])
        )

    if len(list_yml_files) > 1:
        Logger.log(2, "There are more than one metadata file in space with space ID %s" % space_id)
    elif len(list_yml_files) < 1:
        Logger.log(1, "There aren't any metadata file in space with space ID %s" % space_id)
        return file_id, None

    # get metadata file
    yml_file = list_yml_files[0]
    yml_byte_stream = files.downloadFileContent(yml_file["id"])

    data = yaml.load(yml_byte_stream.decode(), Loader=yaml.BaseLoader)
    # yaml = ruamel.yaml.YAML(pure=True) # ruamel
    # data = yaml.load(yml_byte_stream.decode()) # ruamel
    return file_id, data


def setSpaceMetadataFromYaml(space_id):
    Logger.log(4, "setSpaceMetadataFromYaml(%s):" % space_id)
    file_id, data = _loadConfigYAML(space_id)
    return _setFileJsonMetadata(file_id, data)
