from pprint import pprint
import os
import time
import json
import ruamel.yaml
import setting, spaces, storages, metadata, groups, tokens, shares

def scanDirectory(base_path):
    if setting.DEBUG >= 1: print("Processing path", base_path)
    creatingOfSpaces(base_path)
    
    if setting.CONFIG['continousFileImport']['enabled']:
        time.sleep(setting.CONFIG['sleepFactor'])
        setupContinuousImport(base_path)
    if setting.DEBUG >= 1: print("Processing path", base_path, "done.")

def creatingOfSpaces(base_path):
    # pokud obsahuje spa.yml a neni jeste zalozen, tak pro nej zalozit space v OneData

    # get list of existing spaces
    # spaces = list()
    # for space in spaces.getSpaces():
    #     spaces.append(space['name'])

    sub_dirs = os.scandir(path=base_path)
    for directory in sub_dirs:        
        yml_file = directory.path + os.sep + setting.CONFIG['yamlFileName']
        # test if directory is directory and contains a yaml file
        if directory.is_dir() and os.path.isfile(yml_file):
            yml_content = loadYaml(yml_file)
            # test if yaml contains space_id
            if not yamlContainsSpaceId(yml_content):
                if setting.DEBUG >= 1: print("Processing:", base_path + os.sep + directory.name)
                dataset_name = directory.name
                
                # Create storage for space
                storage_id = storages.createAndGetStorage(dataset_name, os.path.join(base_path, directory.name))

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
                    
                    if setting.DEBUG >= 1: print("Processing of", base_path + os.sep + directory.name, "done.")
                else:
                    if setting.DEBUG >= 0: print("Error: Space for", directory.name, "not created.")
            else:
                if setting.DEBUG >= 1: print("Space for", directory.name, "not created (spaceId exists in yaml file).")
        else:
            if setting.DEBUG >= 1: print("Space for", directory.name, "not created (not contains yaml or no dir).")
        time.sleep(setting.CONFIG['sleepFactor'] * 6)

def setupContinuousImport(base_path):
    sub_dirs = os.scandir(path=base_path)
    for directory in sub_dirs:        
        yml_file = directory.path + os.sep + setting.CONFIG['yamlFileName']
        # test if directory is directory and contains a yaml file
        if directory.is_dir() and os.path.isfile(yml_file):
            yml_content = loadYaml(yml_file)
            # test if yaml contains space_id
            space_id = yamlContainsSpaceId(yml_content)
            if space_id:
                running_file = directory.path + os.sep + setting.CONFIG['continousFileImport']['runningFileName']
                # test if directory contains running file
                if os.path.isfile(running_file):
                    spaces.enableContinuousImport(space_id)
                else:
                    spaces.disableContinuousImport(space_id)

def yamlContainsSpaceId(yml_content):
    """
    Test if yaml contains space_id.
    """ 
    yml_spa_space_id = getSpaceIDfromYaml(yml_content)
    if not yml_spa_space_id:
        return False
    else:
        return yml_spa_space_id

def loadYaml(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as stream:
            #configuration = yaml.safe_load(stream) # pyyaml
            yaml = ruamel.yaml.YAML(typ='safe')
            configuration = yaml.load(stream)
            if setting.DEBUG >= 3: pprint(configuration)
            return configuration
    else:
        if setting.DEBUG >= 1: print("Error: File", file_path, "doesn't exists.")

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
        if setting.DEBUG >= 1: print("Error: File", file_path, "doesn't exists.")

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
            #yaml.safe_dump(yaml_dict, f, sort_keys=False)
            
            ryaml = ruamel.yaml.YAML()
            ryaml.width = 200 # count of characters on a line, if there is more chars, line is breaked
            ryaml.indent(sequence=4, offset=2)
            ryaml.dump(yaml_dict, f)
    else:
        if setting.DEBUG >= 1: print("Error: File", file_path, "doesn't exists.")
