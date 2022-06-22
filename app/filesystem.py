from pprint import pprint
import os
import time
import ruamel.yaml
from settings import Settings
from utils import Logger
import spaces, workflow

def scanWatchedDirectories():
    Logger.log(4, "scanWatchedDirectories():")

    for directory in Settings.get().config['watchedDirectories']:
        _scanWatchedDirectory(directory)

def _scanWatchedDirectory(base_path):
    Logger.log(4, "_scanWatchedDirectory(%s):" % base_path)
    Logger.log(3, "Processing path %s" % base_path)

    if not os.path.isdir(base_path):
        Logger.log(1, "Directory %s can't be processed, it doesn't exist." % base_path)
        return

    # creating of spaces and all related stuff
    _creatingOfSpaces(base_path)

    # set continous file import on all spaces
    # TODO, #5 - when config['continousFileImport']['enabled'] is set to False, all import should be stopped
    if Settings.get().config['continousFileImport']['enabled']:
        time.sleep(1 * Settings.get().config['sleepFactor'])
        setupContinuousImport(base_path)

    Logger.log(3, "Processing path %s done." % base_path)

def getMetaDataFile(directory):
    Logger.log(4, "getMetaDataFile(%s):" % directory)
    for file in Settings.get().config['metadataFiles']:
        yml_file = directory.path + os.sep + file
        # check if given metadata file exists in directory
        if os.path.isfile(yml_file):
            # check if a metadata file has been already found
            return yml_file

    # no metadata file found
    Logger.log(4, "No file with metadata found in %s " % directory)
    return None

def _creatingOfSpaces(base_path):
    Logger.log(4, "_creatingOfSpaces(%s):" % base_path)
    sub_dirs = os.scandir(path=base_path)
    # TODO - add condition to process only directories (no files)
    for directory in sub_dirs:
        workflow.registerSpace(base_path, directory)

def setupContinuousImport(base_path):
    Logger.log(4, "setupContinuousImport(%s):" % base_path)
    # TODO, #6 - to be replaced by walk through files in Onedata instead of in POSIX
    sub_dirs = os.scandir(path=base_path)
    for directory in sub_dirs:
        # only directories should be processed
        if not directory.is_dir():
            continue

        # test if directory contains a yaml file
        yml_file = getMetaDataFile(directory)
        if yml_file:
            yml_content = loadYaml(yml_file)
            # test if yaml contains space_id
            space_id = yamlContainsSpaceId(yml_content)
            if space_id:
                # test if such space exists
                try:
                    space_name = spaces.getSpace(space_id)['name']
                except KeyError:
                    Logger.log(1, "Space ID %s found in %s isn't correct." % (space_id, yml_file))
                    return

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
            # if load empty file
            if not configuration:
                configuration = dict()
            
            Logger.log(5, "Configuration:", pretty_print=configuration)
            return configuration
    else:
        Logger.log(1, "File %s doesn't exists." % file_path)

def getSpaceIDfromYaml(yaml_dict):
    """
    Return space_id from YAML file.
    or None when file doesn't contain it.
    """
    if yaml_dict:
        onedata_part = yaml_dict.get(Settings.get().config['metadataFileTags']['onedata'])
        if onedata_part:
            return onedata_part.get(Settings.get().config['metadataFileTags']['space'])

    Logger.log(3, "No onedata tag in YAML")
    return None

def setValueToYaml(file_path, yaml_dict, valueType, value):
    if os.path.exists(file_path):
        if yaml_dict.get(Settings.get().config['metadataFileTags']['onedata']) == None:
            yaml_dict[Settings.get().config['metadataFileTags']['onedata']] = dict()

        # change value in original yaml dict
        if valueType == "Space":
            yaml_dict[Settings.get().config['metadataFileTags']['onedata']][Settings.get().config['metadataFileTags']['space']] = value
        if valueType == "PublicURL":
            yaml_dict[Settings.get().config['metadataFileTags']['onedata']][Settings.get().config['metadataFileTags']['publicURL']] = value
        if valueType == "InviteToken":
            yaml_dict[Settings.get().config['metadataFileTags']['onedata']][Settings.get().config['metadataFileTags']['inviteToken']] = value
        
        # open yaml file
        with open(file_path, 'w') as f:    
            # store new yaml file
            ryaml = ruamel.yaml.YAML()
            ryaml.width = 200 # count of characters on a line, if there is more chars, line is breaked
            ryaml.indent(sequence=4, offset=2)
            ryaml.dump(yaml_dict, f)
    else:
        Logger.log(1, "Metadata file %s doesn't exists." % file_path)

def setValuesToYaml(file_path, yaml_dict, new_values_dict):
    """
    Set values to onedata tag in yaml.
    """
    if os.path.exists(file_path):
        if not yaml_dict.get(Settings.get().config['metadataFileTags']['onedata']):
            # there isn't tag onedata yet
            yaml_dict[Settings.get().config['metadataFileTags']['onedata']] = dict()

        # change value in original yaml dict
        yaml_dict[Settings.get().config['metadataFileTags']['onedata']] = new_values_dict

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
        Logger.log(1, "Metadata file doesn't exists." % file_path)
