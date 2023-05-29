import json
from settings import Settings
from utils import Logger, Utils
import request


def getStorages():
    Logger.log(4, "getStorages():")
    # https://onedata.org/#/home/api/stable/onepanel?anchor=operation/get_storages
    url = "onepanel/provider/storages"
    response = request.get(url)
    return response.json()


def get_storage(storage_id: str) -> dict:
    Logger.log(4, f"get_storage(storage_id={storage_id})")
    # https://onedata.org/#/home/api/21.02.1/onepanel?anchor=operation/get_storage_details
    url = "onepanel/provider/storages/" + storage_id
    response = request.get(url)

    if not response.ok:
        Logger.log(3, f"Cannot get information about storage with id {storage_id}")
        return {}

    return response.json()


def getLastStorage():
    Logger.log(4, "getLastStorage():")
    storages = getStorages()
    if len(storages["ids"]) == 0:
        Logger.log(2, "Found 0 storages")
    Logger.log(4, "Get last storage = %s" % storages["ids"][0:1])
    return storages["ids"][0]


def add_storage(name: str, mountpoint: str) -> dict:
    Logger.log(4, f"add_storage(name={name}, mp={mountpoint}):")
    # https://onedata.org/#/home/api/21.02.1/onepanel?anchor=operation/add_storage

    url = "onepanel/provider/storages"
    data = {
        name: {"type": "posix", "importedStorage": True, "readonly": True, "mountPoint": mountpoint}
    }
    headers = dict({"Content-type": "application/json"})
    resp = request.post(url, headers=headers, data=json.dumps(data))

    if resp.status_code == 200:
        return resp.json()
    return {}


def getStorageDetails(storage_id):
    Logger.log(4, "getStorageDetails(%s)" % storage_id)
    url = "onepanel/provider/storages/" + storage_id
    response = request.get(url)
    # todo: doklepat, neverit ze dostaneme stale token
    if response.status_code == 404:
        return False
    return response.json()


def get_storage_id_by_name(name: str) -> str:
    for storage_id in getStorages()["ids"]:
        storage = getStorageDetails(storage_id)
        if storage["name"].startswith(name):
            return storage_id

    return ""


def create_and_get_storage(name: str, mount_point: str) -> str:
    """
    Creates storage and returns its ID.
    If some error occurred, returns empty string
    """
    Logger.log(4, f"create_and_get_storage(name={name}, mp={mount_point}):")

    if len(name) < Settings.get().MIN_ONEDATA_NAME_LENGTH:
        Logger.log(1, f"Too short storage name {name}.")
        return ""

    new_name = Utils.clearOnedataName(name)

    storage_identification = add_storage(new_name, mount_point)

    if not storage_identification:
        Logger.log(1, f"Storage with name {new_name} could not be created.")
        return ""

    name_list = list(storage_identification.keys())

    if len(name_list) == 0:
        Logger.log(1, f"Storage with desired name {new_name} was not created due unexpected error.")
        return ""

    returned_name = name_list[0]
    storage_id = storage_identification[returned_name].get("id", "")

    if not storage_id:
        Logger.log(1, f"Storage with desired name {new_name} was not created; did not return id.")
        return ""

    # compare names of storages, compare cleared names
    if returned_name != name:
        Logger.log(3, f"Storage of desired name {name} was created with name {returned_name} and id {storage_id}")
        return storage_id

    Logger.log(3, f"Storage {name} was created with id {storage_id}")
    return storage_id


def removeStorage(storage_id):
    Logger.log(4, "removeStorage(%s)" % storage_id)
    url = "onepanel/provider/storages/" + storage_id
    response = request.delete(url)
    return response
