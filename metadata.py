import json
import yaml
from setting import *
from spaces import *

def setFileJsonMetadata(file_id, data):
    if DEBUG: print("setFileJsonMetadata(" + file_id + ", data): ")
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/set_json_metadata
    url = ONEPROVIDER_API_URL + "oneprovider/data/" + file_id + "/metadata/json"
    
    headers = dict(ONEZONE_AUTH_HEADERS)
    headers['Content-type'] = 'application/json'
    resp = requests.put(url, headers=headers, data=json.dumps(data), verify=False)
    return resp

def setSpaceMetadataFromYml(space_id):
    if DEBUG: print("setSpaceMetadataFromYml(" + space_id + "): ")
    # get file_id of space dir
    res = getSpace(space_id)
    file_id = res['fileId']

    # find ymls
    res = listDirectory(file_id)
    list_yml_files = list(filter(lambda x: ".yml" in x['name'], res['children']))

    for yml_file in list_yml_files:
        yml_file_id = yml_file['id']
        yml_byte_stream = downloadFileContent(yml_file_id).content
        
        data = yaml.load(yml_byte_stream.decode(), Loader=yaml.BaseLoader)
        
        if DEBUG: pprint(data)
        # musi se pridat zachovani uz existujiciho pripadneho JSONu
        setFileJsonMetadata(file_id, data)
        