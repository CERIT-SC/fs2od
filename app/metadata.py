from pprint import pprint
import json
import yaml
import setting, spaces, files, request

def setFileJsonMetadata(file_id, data):
    if setting.DEBUG >= 2: print("setFileJsonMetadata(" + file_id + ", data): ")
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/set_json_metadata
    url = "oneprovider/data/" + file_id + "/metadata/json"
    headers = dict({'Content-type': 'application/json'})
    response = request.put(url, headers=headers, data=json.dumps(data))
    return response

def setSpaceMetadataFromYml(space_id):
    if setting.DEBUG >= 2: print("setSpaceMetadataFromYml(" + space_id + "): ")
    # get file_id of space dir
    space = spaces.getSpace(space_id)
    file_id = space['fileId']

    # find ymls
    space_content = files.listDirectory(file_id)
    list_yml_files = list(filter(lambda x: ".yml" in x['name'], space_content['children']))

    for yml_file in list_yml_files:
        yml_file_id = yml_file['id']
        yml_byte_stream = files.downloadFileContent(yml_file_id).content
        
        data = yaml.load(yml_byte_stream.decode(), Loader=yaml.BaseLoader)
        #yaml = ruamel.yaml.YAML(pure=True) # ruamel
        #data = yaml.load(yml_byte_stream.decode()) # ruamel
        
        if setting.DEBUG >= 3: pprint(data)
        # musi se pridat zachovani uz existujiciho pripadneho JSONu
        setFileJsonMetadata(file_id, data)
        