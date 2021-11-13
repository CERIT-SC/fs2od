from pprint import pprint
import json
import yaml
from settings import Settings
import spaces, files, request

def setSpaceMetadataFromJSON(file_id, data):
    if Settings.get().debug >= 2: print("setFileJsonMetadata(" + file_id + ", data): ")
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/set_json_metadata
    url = "oneprovider/data/" + file_id + "/metadata/json"
    headers = dict({'Content-type': 'application/json'})
    response = request.put(url, headers=headers, data=json.dumps(data))
    return response.ok

def loadConfigYAML(space_id):
    """
    Load configuration YAML file from root directory of space and return its file_id and content.
    Return None if such file doesn't exist.
    """
    # get file_id of space dir
    space = spaces.getSpace(space_id)
    file_id = space['fileId']

    # find ymls
    space_content = files.listDirectory(file_id)
    list_yml_files = list(filter(lambda x: Settings.get().config['yamlFileName'] in x['name'], space_content['children']))

    # in case there are more than one such file (should not happend) it return the first one
    for yml_file in list_yml_files:
        yml_byte_stream = files.downloadFileContent(yml_file['id'])
        
        data = yaml.load(yml_byte_stream.decode(), Loader=yaml.BaseLoader)
        #yaml = ruamel.yaml.YAML(pure=True) # ruamel
        #data = yaml.load(yml_byte_stream.decode()) # ruamel
        return file_id, data

    # no config YAML found
    return None

def setSpaceMetadataFromYaml(space_id):
    if Settings.get().debug >= 2: print("setSpaceMetadataFromYaml(" + space_id + "): ")
    file_id, data = loadConfigYAML(space_id)
    setSpaceMetadataFromJSON(file_id, data)
