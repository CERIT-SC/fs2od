import json
import request
from settings import Settings

def getFileAttributes(file_id):
    """
    Get attributes of file with given file_id.
    """
    if Settings.get().debug >= 2: print("getFileAttributes(" + file_id + "): ")
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/get_attrs
    url = "oneprovider/data/" + file_id
    response = request.get(url)
    return response.json()

def setFileAttribute(file_id, posix_mode):
    """
    Set attributes to directory or file with given file_id. Only POSIX mode can be set up.
    """
    if Settings.get().debug >= 2: print("setFileAttribute(" + file_id + ", " + posix_mode + "): ")
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/set_attr
    url = "oneprovider/data/" + file_id
    data = {
        'mode': posix_mode
    }
    headers = dict({'Content-type': 'application/json'})
    response = request.put(url, headers=headers, data=json.dumps(data))
    return response.ok

def setFileAttributeRecursive(file_id, posix_mode):
    """
    Set attributes to directory or file with given file_id. Only POSIX mode can be set up. 
    In case of directory attributes is set to all children.
    """
    attributes = getFileAttributes(file_id)

    if not 'type' in attributes:
        # in case there is no file in space
        return

    if attributes['type'] == "dir":
        # node is directory
        directory = listDirectory(file_id)
        for node in directory['children']:
            # recursive set up attributes to all files in directory
            setFileAttributeRecursive(node['id'], posix_mode)
    else:
        # node is file
        setFileAttribute(file_id, posix_mode)

def listDirectory(file_id):
    """
    List directory. Subdirectories and files are accesible in response['children'].
    """
    if Settings.get().debug >= 2: print("listDirectory(" + file_id + "): ")
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/list_children
    url = "oneprovider/data/" + file_id + "/children"
    response = request.get(url)
    return response.json()

def downloadFileContent(file_id):
    """
    Download file conntent as binary string (application/octet-stream).
 
    """
    if Settings.get().debug >= 2: print("downloadFileContent(" + file_id + "): ")
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/download_file_content
    url = "oneprovider/data/" + file_id + "/content"
    response = request.get(url)
    return response.content

def lookupFileId(path):
    """
    Return file_id of file with given path in format e.g. 
    '/MySpace/dir/readme.txt'
    Return None if path doesn't exist.
    """
    if Settings.get().debug >= 2: print("filePathResolution(" + path + "): ")
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=tag/File-Path-Resolution
    url = "oneprovider/lookup-file-id/" + path
    response = request.post(url)
    if response.ok:
        return response.json()
    else:
        if Settings.get().debug >= 1: print("Warning: lookupFileId return not ok response - ", response.text)
        return None