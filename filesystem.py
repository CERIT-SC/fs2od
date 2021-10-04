from pprint import pprint
import yaml
import os
import time
import json
import setting, spaces, storages, metadata, groups, tokens, shares

def scanDirectory(base_path):
    creatingOfSpaces(base_path)
    time.sleep(setting.CONFIG['sleepFactor'])
    #setupContinuousImport(base_path)
    
def creatingOfSpaces(base_path):
    # pokud obsahuje spa.yml a neni jeste zalozen, tak pro nej zalozit space v OneData

    # get list of existing spaces
    # spaces = list()
    # for space in spaces.getSpaces():
    #     spaces.append(space['name'])

    sub_dirs = os.scandir(path=base_path)
    for d in sub_dirs: 
        
        yml_file = d.path + os.sep + setting.CONFIG['yamlFileName']
        yml_spa_exists = os.path.isfile(yml_file)
        # if file exists and contains yaml file
        if d.is_dir() and yml_spa_exists:
            yml_content = loadYaml(yml_file)
            yml_spa_space_id = getSpaceIDfromYaml(yml_content)
            # if space_id isn't in the file
            if not yml_spa_space_id:
                print("Processing: ", base_path + os.sep + d.name)
                dataset_name = d.name
                # Create storage for space
                storage_id = storages.createAndGetStorage(dataset_name, base_path + d.name)

                # Create group for space
                gid = groups.createChildGroup(setting.CONFIG['spacesParentGroupId'], dataset_name)
                time.sleep(2)

                # Create invite token for the group
                token = tokens.createInviteTokenToGroup(gid, "Invite token for " + dataset_name)
                time.sleep(2)

                # Create space
                space_id = spaces.createAndSupportSpaceForGroup(dataset_name, gid, storage_id, setting.CONFIG['implicitSpaceSize'])
                time.sleep(5)
                if space_id:
                    print("space id = " + space_id)
                    # Set metadata for the space
                    metadata.setSpaceMetadataFromYml(space_id)

                    # Create public share
                    file_id = spaces.getSpace(space_id)['fileId']
                    description = """
                    = Lorem
                    Lorem ipsum dolor sit amet, consectetur adipiscing
                    * Click on Files
                    * You will see files
                    """
                    share = shares.createAndGetShare(dataset_name, file_id, description)

                    # write onedata parameters to file
                    yaml_onedata_dict = dict()
                    yaml_onedata_dict['space'] = space_id
                    yaml_onedata_dict['publicURL'] = share['publicUrl']
                    yaml_onedata_dict['inviteToken'] = token['token']
                    setValuesToYaml(yml_file, yml_content, yaml_onedata_dict)
                    # setValueToYaml(yml_file, yml_content, "publicURL", share['publicUrl'])
                    # setValueToYaml(yml_file, yml_content, "inviteToken", token['token'])
                    # setValueToYaml(yml_file, yml_content, "space", space_id)
                else:
                    print("Space for", d.name, "not created (error).")
            else:
                print("Space for", d.name, "not created (spaceId exists).")
        else:
            print("Space for", d.name, "not created.")
        time.sleep(setting.CONFIG['sleepFactor'] * 6)

def removingOfSpaceASpol(space_id):
    # odstraneni invite tokenu
    # odstraneni skupiny
    # odstraneni space
    # odstraneni storage
    pass

def setupContinuousImport(base_path):
    sub_dirs = os.scandir(path=base_path)
    for d in sub_dirs:
        if os.path.isfile(d.path + "/onedata.yml"):
            with open(d.path + '/onedata.yml', "r") as json_file:
                space_data = json.load(json_file)
                space_id = space_data['onedata']['spaceId']

            if space_id:
                if os.path.isfile(d.path + "/.running"):
                    spaces.enableContinuousImport(space_id)
                else:
                    spaces.disableContinuousImport(space_id)

def loadYaml(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as stream:
            configuration = yaml.safe_load(stream)
            if setting.DEBUG >= 3: pprint(configuration)
            return configuration
    else:
        print("File", file_path, "doesn't exists.")

def getSpaceIDfromYaml(yaml_dict):
    onedata_part = yaml_dict.get('onedata')
    if onedata_part:
        return onedata_part.get('space')
    return None

def setValueToYaml(file_path, yaml_dict, valueType, value):    
    if os.path.exists(file_path):
        if yaml_dict.get('onedata') == None:
            yaml_dict['onedata'] = dict()
        # change value in original yaml dict
        if valueType == "space":
            yaml_dict['onedata']['space'] = value
        if valueType == "publicURL":
            yaml_dict['onedata']['publicURL'] = value
        if valueType == "inviteToken":
            yaml_dict['onedata']['inviteToken'] = value
        
        # open yaml file
        with open(file_path, 'w') as f:    
            # store new yaml file
            yaml.safe_dump(yaml_dict, f, sort_keys=False)
    else:
        print("File", file_path, "doesn't exists.")

def setValuesToYaml(file_path, yaml_dict, new_values_dict):
    """
    Set values to onedata tag in yaml. 

    """
    if os.path.exists(file_path):
        if yaml_dict.get('onedata') == None:
            yaml_dict['onedata'] = dict()
        # change value in original yaml dict
        yaml_dict['onedata'] = new_values_dict

        # open yaml file
        with open(file_path, 'w') as f:    
            # store new yaml file
            # Solving bad indentation of list
            # https://stackoverflow.com/questions/25108581/python-yaml-dump-bad-indentation
            yaml.safe_dump(yaml_dict, f, sort_keys=False)
    else:
        print("File", file_path, "doesn't exists.")
