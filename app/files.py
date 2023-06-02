import json
import request
from settings import Settings
from utils import Logger


def getFileAttributes(file_id):
    """
    Get attributes of file with given file_id.
    """
    Logger.log(5, "getFileAttributes(%s):" % file_id)
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/get_attrs
    url = "oneprovider/data/" + file_id
    response = request.get(url)
    return response.json()


def setFileAttribute(file_id, posix_mode) -> bool:
    """
    Set attributes to directory or file with given file_id. Only POSIX mode can be set up.
    """
    Logger.log(5, "setFileAttribute(%s, %s):" % (file_id, posix_mode))
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/set_attr
    url = "oneprovider/data/" + file_id
    data = {"mode": posix_mode}
    headers = dict({"Content-type": "application/json"})
    response = request.put(url, headers=headers, data=json.dumps(data))
    return response.ok


def setFileAttributeRecursive(file_id: str, posix_mode: str) -> bool:
    """
    Set attributes to directory or file with given file_id. Only POSIX mode can be set up.
    In case of directory attributes is set to all children.
    Returns True if everything was successful, otherwise False
    """
    Logger.log(5, "setFileAttributeRecursive(%s, %s):" % (file_id, posix_mode))
    attributes = getFileAttributes(file_id)
    successful = True

    if not "type" in attributes:
        # in case there is no file in space
        # TODO: could this case happen? Check.
        return True

    if attributes["type"].lower() == "dir":
        # node is directory
        if attributes["mode"] != posix_mode:
            # desired posix_mode is different from the actual mode
            # set attribute to directory itself
            successful = setFileAttribute(file_id, posix_mode) and successful

        # set attribute to childs
        directory = listDirectory(file_id)
        for node in directory["children"]:
            # recursive set up attributes to all files in directory
            successful = setFileAttributeRecursive(node["file_id"], posix_mode) and successful
    else:
        # node is file
        if attributes["mode"] != posix_mode:
            # desired posix_mode is different from the actual mode
            successful = setFileAttribute(file_id, posix_mode) and successful

    return successful


def listDirectory(file_id):
    """
    List directory. Subdirectories and files are accesible in response['children'].
    """
    Logger.log(5, "listDirectory(%s):" % file_id)
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/list_children
    url = "oneprovider/data/" + file_id + "/children"
    response = request.get(url)
    return response.json()


def downloadFileContent(file_id):
    """
    Download file conntent as binary string (application/octet-stream).
    """
    Logger.log(4, "downloadFileContent(%s):" % file_id)
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/download_file_content
    url = "oneprovider/data/" + file_id + "/content"
    response = request.get(url)
    if response.ok:
        return response.content


def lookup_file_id(path) -> str:
    """
    Return file_id of file with given path in format e.g.
    '/MySpace/dir/readme.txt'
    Return empty string if path doesn't exist.
    """
    Logger.log(4, "lookup_file_id(%s):" % path)
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=tag/File-Path-Resolution
    url = "oneprovider/lookup-file-id/" + path
    response = request.post(url)
    if response.ok:
        return response.json()["fileId"]
    else:
        Logger.log(2, "lookup_file_id return not ok response: %s" % response.text)
        return ""


def get_id_of_file_in_directory(directory_file_id: str, searched_file_name: str, oneprovider_index: int = 0) -> str:
    """
    Returns file id of searched file. If not in directory, returns empty string
    """
    Logger.log(5, f"get_id_of_file_in_directory(dir_fileid={directory_file_id},"
                  f"search_filename={searched_file_name},oneprovider_index={oneprovider_index}):")
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/list_children
    url = "oneprovider/data/" + directory_file_id + "/children"

    still_searching = True
    offset = 0
    while still_searching:
        response = request.get(
            url=url + f"?attribute=file_id&attribute=name&limit=1000&offset={offset}",
            oneprovider_index=oneprovider_index
        )

        if not response.ok:
            Logger.log(3, f"Getting children of directory with file id {directory_file_id} not successful.")
            return ""
        response_json = response.json()
        children = response_json["children"]

        for child in children:
            if child["name"] == searched_file_name:
                return child["file_id"]

        offset += 1000
        still_searching = not response_json["isLast"]

    return ""


