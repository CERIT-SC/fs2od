from pprint import pprint
import os
import time
import ruamel.yaml
from settings import Settings
import spaces, storages, metadata, groups, tokens, shares, files

def scanWatchedDirectories():
    if Settings.get().debug >= 2: print("Directories to check:")
    if Settings.get().debug >= 2: pprint(Settings.get().config['watchedDirectories'])

    for d in Settings.get().config['watchedDirectories']:
        scanDirectory(d)

def scanDirectory(base_path):
    if Settings.get().debug >= 1: print("Processing path", base_path)
    creatingOfSpaces(base_path)
    
    # if Settings.get().config['continousFileImport']['enabled']:
    if Settings.get().config['continousFileImport']['enabled']:  ########################################
        time.sleep(Settings.get().config['sleepFactor'])
        setupContinuousImport(base_path)
    if Settings.get().debug >= 1: print("Processing path", base_path, "done.")

def creatingOfSpaces(base_path):
    # pokud obsahuje spa.yml a neni jeste zalozen, tak pro nej zalozit space v OneData

    # get list of existing spaces
    # spaces = list()
    # for space in spaces.getSpaces():
    #     spaces.append(space['name'])

    sub_dirs = os.scandir(path=base_path)
    for directory in sub_dirs:        
        yml_file = directory.path + os.sep + Settings.get().config['yamlFileName']
        # test if directory is directory and contains a yaml file
        if directory.is_dir() and os.path.isfile(yml_file):
            yml_content = loadYaml(yml_file)
            # test if yaml contains space_id
            if not yamlContainsSpaceId(yml_content):
                if Settings.get().debug >= 1: print("Processing:", base_path + os.sep + directory.name)
                dataset_name = directory.name
                
                # Create storage for space
                storage_id = storages.createAndGetStorage(dataset_name, os.path.join(base_path, directory.name))

                # Create group for space
                #gid = groups.createChildGroup(Settings.get().config['spacesParentGroupId'], dataset_name)
                gid = groups.createParentGroup(Settings.get().config['initialGroupId'], dataset_name)
                time.sleep(1)

                # Create invite token for the group
                token = tokens.createInviteTokenToGroup(gid, "Invite token for " + dataset_name)
                time.sleep(1)

                # Create a new space
                space_id = spaces.createSpaceForGroup(gid, dataset_name)
                support_token = tokens.createNamedTokenForUser(space_id, dataset_name, Settings.get().config['serviceUserId'])
                time.sleep(3)
                if space_id and support_token:
                    # write onedata parameters (space_id, invite_token) to file
                    yaml_onedata_dict = dict()
                    yaml_onedata_dict['Space'] = space_id
                    yaml_onedata_dict['InviteToken'] = token['token']
                    setValuesToYaml(yml_file, yml_content, yaml_onedata_dict)

                    # set up space support on the provider
                    spaces.supportSpace(support_token, Settings.get().config['implicitSpaceSize'], storage_id)
                    tokens.deleteNamedToken(support_token['tokenId'])
                    time.sleep(3)

                    # Create public share
                    file_id = spaces.getSpace(space_id)['fileId']
                    description = ""
                    share = shares.createAndGetShare(dataset_name, file_id, description)

                    # write onedata parameter (publicURL) to file
                    setValueToYaml(yml_file, yml_content, "PublicURL", share['publicUrl'])
                    time.sleep(1)

                    # Set metadata for the space
                    metadata.setSpaceMetadataFromYaml(space_id)

                    # set up permissions
                    files.setFileAttributeRecursive(file_id, Settings.get().config['initialPOSIXlikePermissions'])

                    if Settings.get().debug >= 1: print("Processing of", base_path + os.sep + directory.name, "done.")
                else:
                    if Settings.get().debug >= 0: print("Error: Space for", directory.name, "not created.")
            else:
                if Settings.get().debug >= 1: print("Space for", directory.name, "not created (spaceId exists in yaml file).")
        else:
            if Settings.get().debug >= 1: print("Space for", directory.name, "not created (not contains yaml or no dir).")
        time.sleep(Settings.get().config['sleepFactor'] * 6)

def setupContinuousImport(base_path):
    sub_dirs = os.scandir(path=base_path)
    for directory in sub_dirs:        
        yml_file = directory.path + os.sep + Settings.get().config['yamlFileName']
        # test if directory is directory and contains a yaml file
        if directory.is_dir() and os.path.isfile(yml_file):
            yml_content = loadYaml(yml_file)
            # test if yaml contains space_id
            space_id = yamlContainsSpaceId(yml_content)
            if space_id:
                running_file = directory.path + os.sep + Settings.get().config['continousFileImport']['runningFileName']
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
            if Settings.get().debug >= 3: pprint(configuration)
            return configuration
    else:
        if Settings.get().debug >= 1: print("Error: File", file_path, "doesn't exists.")

def getSpaceIDfromYaml(yaml_dict):
    """
    Return space_id from YAML file.
    or None when file doesn't contain it.
    """
    if yaml_dict:
        onedata_part = yaml_dict.get('Onedata')
        if onedata_part:
            return onedata_part.get('Space')
    # no onedata or space tag in YAML
    return None

def setValueToYaml(file_path, yaml_dict, valueType, value):
    if os.path.exists(file_path):
        if yaml_dict.get('Onedata') == None:
            yaml_dict['Onedata'] = dict()
        # change value in original yaml dict
        if valueType == "Space":
            yaml_dict['Onedata']['Space'] = value
        if valueType == "PublicURL":
            yaml_dict['Onedata']['PublicURL'] = value
        if valueType == "InviteToken":
            yaml_dict['Onedata']['InviteToken'] = value
        
        # open yaml file
        with open(file_path, 'w') as f:    
            # store new yaml file
            ryaml = ruamel.yaml.YAML()
            ryaml.width = 200 # count of characters on a line, if there is more chars, line is breaked
            ryaml.indent(sequence=4, offset=2)
            ryaml.dump(yaml_dict, f)
    else:
        if Settings.get().debug >= 1: print("Error: File", file_path, "doesn't exists.")

def setValuesToYaml(file_path, yaml_dict, new_values_dict):
    """
    Set values to onedata tag in yaml. 

    """
    if os.path.exists(file_path):
        if yaml_dict.get('Onedata') == None:
            yaml_dict['Onedata'] = dict()
        # change value in original yaml dict
        yaml_dict['Onedata'] = new_values_dict

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
        if Settings.get().debug >= 1: print("Error: File", file_path, "doesn't exists.")
