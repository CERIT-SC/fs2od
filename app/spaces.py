import json
import time
import storages
import filesystem
from settings import Settings
from utils import Logger, Utils
import request, tokens, files, metadata, dareg

"""
Minimal size of a space. Smaller size cause "badValueTooLow" error on Oneprovder. 
1 MB = 1*2**20 = 1048576
"""
MINIMAL_SPACE_SIZE = 1048576


def getSpaces(oneprovider_index: int = 0):
    Logger.log(4, f"getSpaces(order={oneprovider_index}):")
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/get_all_spaces
    url = f"oneprovider/spaces"
    response = request.get(url, oneprovider_index=oneprovider_index)
    return response.json()


def removeSpace(space_id):
    Logger.log(4, "removeSpace(%s):" % space_id)
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/remove_space
    url = "onezone/spaces/" + space_id
    response = request.delete(url)
    return response


def get_space(space_id: str, ok_statuses: tuple = (200,)) -> dict:
    """
    Returns the basic information about space with given id.
    If response is not ok, but accepted by ok_statuses, returns {"spaceId": "allowed_ok_status"}
    joined with response from server
    Otherwise returns empty dict
    """
    Logger.log(4, f"get_space({space_id},ok_statuses={ok_statuses}):")
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/get_space
    url = "oneprovider/spaces/" + space_id
    response = request.get(url, ok_statuses=ok_statuses)
    if response.ok:
        return response.json()
    elif response.status_code in ok_statuses:
        response = response.json()
        response["spaceId"] = "allowed_ok_status"
        return response
    else:
        return {}


def get_space_mount_point(space_id: str, oneprovider_index=0) -> str:
    """
    Returns mount point of a storage provided by given Oneprovider for space
    If there is no support or storage is not of POSIX type, returns empty string
    """
    Logger.log(4, f"get_space_primary_mount_point(space_id={space_id},op_index={oneprovider_index})")

    # space details must be from onepanel
    space_details = getSpaceDetails(space_id, oneprovider_index=oneprovider_index)
    if not space_details or "storageId" not in space_details:
        return ""

    storage_id = space_details["storageId"]
    storage_details = storages.get_storage(storage_id)

    if not storage_details:
        return ""

    if storage_details.get("type", "") != "posix" or not storage_details.get("mountPoint", ""):
        Logger.log(4, f"Space with id {space_id} on {Settings.get().ONEPROVIDERS_DOMAIN_NAMES[oneprovider_index]} "
                      f"and its storage with id {storage_id} is not a POSIX storage")
        return ""

    return storage_details["mountPoint"]


def space_exists(space_id: str) -> bool:
    Logger.log(4, f"space_exists({space_id}):")
    response_dict = get_space(space_id, ok_statuses=(200, 403))

    return not bool(response_dict.get("error", False))


def get_space_from_onezone(space_id) -> dict:
    """
    Returns the basic information about space with given Id.
    """
    Logger.log(4, f"get_space_from_onezone({space_id}):")
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/get_space
    url = "onezone/spaces/" + space_id
    response = request.get(url)
    if response.status_code == 404:
        return {}
    return response.json()


def get_space_id_by_name(name: str) -> str:
    Logger.log(4, f"get_space_id_by_name({name}):")
    for space in getSpaces():
        if space["name"].startswith(name):
            return space["spaceId"]
    return ""


def getSpaceDetails(space_id, oneprovider_index: int = 0):
    Logger.log(4, f"getSpaceDetails(space_id={space_id},op_index={oneprovider_index})")
    # https://onedata.org/#/home/api/stable/onepanel?anchor=operation/get_space_details
    url = "onepanel/provider/spaces/" + space_id
    response = request.get(url, oneprovider_index=oneprovider_index)

    # not supported, non-existent or forbidden
    if not response.ok:
        Logger.log(3, f"Space with id {space_id} is not supported by "
                      f"{Settings.get().ONEPROVIDERS_DOMAIN_NAMES[oneprovider_index]}")
        return {}

    return response.json()


def getAutoStorageImportInfo(space_id):
    Logger.log(4, "getAutoStorageImportInfo(%s):" % space_id)
    # https://onedata.org/#/home/api/stable/onepanel?anchor=operation/get_auto_storage_import_info
    url = "onepanel/provider/spaces/" + space_id + "/storage-import/auto/info"
    response = request.get(url)
    return response.json()


def startAutoStorageImport(space_id) -> bool:
    Logger.log(4, "startAutoStorageImport(%s):" % space_id)
    # https://onedata.org/#/home/api/stable/onepanel?anchor=operation/force_start_auto_storage_import_scan
    url = "onepanel/provider/spaces/" + space_id + "/storage-import/auto/force-start"
    
    response = request.post(url, ok_statuses=(409,))

    status = response.ok or response.status_code == 409

    if response.ok:
        Logger.log(3, f"Auto storage import for space {space_id} started")
    elif response.status_code == 409:
        Logger.log(3, f"Auto storage import for space {space_id} is currently executed")
    else:
        Logger.log(1, f"Auto storage import for space {space_id} failed")

    return status


def stopAutoStorageImport(space_id):
    Logger.log(4, "stopAutoStorageImport(%s):" % space_id)
    # https://onedata.org/#/home/api/stable/onepanel?anchor=operation/force_start_auto_storage_import_scan
    url = "onepanel/provider/spaces/" + space_id + "/storage-import/auto/force-stop"
    response = request.post(url)
    return response


def createSpaceForGroup(group_id, space_name):
    Logger.log(4, "createSpaceForGroup(%s, %s):" % (group_id, space_name))

    if len(space_name) < Settings.get().MIN_ONEDATA_NAME_LENGTH:
        Logger.log(1, "Too short space name %s." % space_name)
        return

    space_name = Utils.clearOnedataName(space_name)

    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/create_space_for_group
    url = "onezone/groups/" + group_id + "/spaces"
    my_data = {"name": space_name}
    headers = dict({"Content-type": "application/json"})
    response = request.post(url, headers=headers, data=json.dumps(my_data))
    # Should return space ID in Headers
    location = response.headers["Location"]
    space_id = location.split("spaces/")[1]
    if space_id:
        Logger.log(
            3, "Space %s was created with space ID %s" % (space_name, space_id), space_id=space_id
        )
        return space_id
    else:
        Logger.log(1, "Space %s can't be created" % space_name)


def supportSpace(token, size, storage_id, space_id, oneprovider_index: int = 0) -> str:
    Logger.log(4, f"supportSpace(token={token}, size={size}, storage_id={storage_id})")
    Logger.log(3, f"Atempt to set up support to space with id {space_id} for "
                  f"{Settings.get().ONEPROVIDERS_DOMAIN_NAMES[oneprovider_index]}")
    # https://onedata.org/#/home/api/stable/onepanel?anchor=operation/support_space
    url = f"onepanel/provider/spaces"
    data = {
        "token": token,
        "size": size,
        "storageId": storage_id,
        "storageImport": {
            "mode": "auto",
            "autoStorageImportConfig": {
                "continuousScan": Settings.get().config["continousFileImport"]["enabled"],
                "scanInterval": Settings.get().config["continousFileImport"]["scanInterval"],
                "detectModifications": Settings.get().config["continousFileImport"][
                    "detectModifications"
                ],
                "detectDeletions": Settings.get().config["continousFileImport"]["detectDeletions"],
            },
        },
    }

    headers = dict({"Content-type": "application/json"})
    response = request.post(url, headers=headers, data=json.dumps(data), oneprovider_index=oneprovider_index)
    if response.ok:
        Logger.log(3, "Support of space %s successfully set on storage %s" % (space_id, storage_id))
        return response.json()["id"]
    else:
        Logger.log(1, "Space support can't be set on storage %s" % storage_id)
        return ""


def revoke_space_support(space_id: str, oneprovider_index: int = 0) -> bool:
    """
    Revokes space support for Oneprovider. If none given in parameter, revoking for primary Oneprovider
    Returns true or false based on successfulness of this operation.
    Not revoking support due to non-existent space id on this provider is considered as successful operation
    """
    Logger.log(4, f"revokeSpaceSupport(space_id={space_id},oneprovider_index={oneprovider_index}):")
    # https://onedata.org/#/home/api/stable/onepanel?anchor=operation/revoke_space_support
    url = "onepanel/provider/spaces/" + space_id
    response = request.delete(url, ok_statuses=(204, 404), oneprovider_index=oneprovider_index)
    if response.ok or response.status_code == 404:
        Logger.log(3, f"Space {space_id} support revoked")
        return True
    else:
        Logger.log(1, f"Error when revoking space {space_id} support")
        return False


def setSpaceSize(space_id, size=None):
    """
    Set a new given size to space with given space_id.
    If size is not set, it set up a new size of space to be equal to actual space occupancy.
    """
    Logger.log(4, "setSpaceSize(%s, %s):" % (space_id, str(size)))
    # if size not set, get spaceOccupancy
    if not size:
        sd = getSpaceDetails(space_id)
        size = sd["spaceOccupancy"]

    # fix space size if it is too small
    if size < MINIMAL_SPACE_SIZE:
        Logger.log(3, "Space size fixed (%s -> %s)" % (size, MINIMAL_SPACE_SIZE))
        size = MINIMAL_SPACE_SIZE

    number_of_affected_providers = 1
    # when data replication is enabled, setting space size (size of support) for each of supporting providers
    if Settings.get().DATA_REPLICATION_ENABLED:
        number_of_affected_providers = len(Settings.get().ONEPROVIDERS_AUTH_HEADERS)

    response = None
    # goes down because response of provider 0 is important
    for oneprovider_index in range(number_of_affected_providers - 1, -1, -1):
        # based on https://onedata.org/#/home/api/stable/onepanel?anchor=operation/modify_space
        url = f"onepanel/provider/spaces/" + space_id
        data = {"size": size}
        headers = dict({"Content-type": "application/json"})
        response = request.patch(url, headers=headers, data=json.dumps(data), oneprovider_index=oneprovider_index)
        provider_domain_name = Settings.get().ONEPROVIDERS_DOMAIN_NAMES[oneprovider_index]
        if response.ok:
            # Logger.log(3, "New size (%s) set for space %s" % (size, space_id), space_id=space_id)
            Logger.log(3, "New size (%s) set for storage of provider %s in space %s" % (
            size, provider_domain_name, space_id), space_id=space_id)
            # dareg.log(space_id, "info", "set new size %s" % size)
            dareg.log(space_id, "info", "set new size %s for storage of provider %s" % (size, provider_domain_name))
        else:
            Logger.log(
                2, "New size (%s) can't be set for storage of provider %s of space %s" % (
                size, provider_domain_name, space_id), space_id=space_id
            )
        time.sleep(1 * Settings.get().config["sleepFactor"])
    return response


def createAndSupportSpaceForGroup(name, group_id, storage_id, capacity):
    Logger.log(4, "createAndSupportSpaceForGroup(%s, group_id, storage_id, capacity):" % name)
    space_id = createSpaceForGroup(group_id, name)
    token = tokens.createNamedTokenForUser(space_id, name, Settings.get().config["serviceUserId"])
    time.sleep(3 * Settings.get().config["sleepFactor"])
    supportSpace(token, capacity, storage_id, space_id)
    tokens.deleteNamedToken(token["tokenId"])
    return space_id


def enableContinuousImport(space_id):
    Logger.log(4, "enableContinuousImport(%s):" % space_id)
    # not doing anymore in filesystem due to variety options
    # running file exists, permissions should be periodically set to new dirs and files have given permissions
    # but first filesystem
    # mount_point = get_space_mount_point(space_id)
    # filesystem.chmod_recursive(mount_point, Settings.get().config["i3nitialPOSIXlikePermissions"])

    posix_mode_string = oct(Settings.get().config["initialPOSIXlikePermissions"])
    if posix_mode_string.startswith("0o"):
        posix_mode_string = posix_mode_string[2:]

    file_id = get_space(space_id)["fileId"]
    files.setFileAttributeRecursive(file_id, posix_mode_string)

    if not getContinuousImportStatus(space_id):
        setSpaceSize(space_id, Settings.get().config["implicitSpaceSize"])
        time.sleep(1 * Settings.get().config["sleepFactor"])
        result = setContinuousImport(space_id, True)
        if result:
            Logger.log(
                3, "Continuous import enabled for space with ID %s" % space_id, space_id=space_id
            )
            dareg.log(space_id, "info", "continuous scan enabled")
            # continous import is enabled now
            # force (full) import of files immediately
            time.sleep(1 * Settings.get().config["sleepFactor"])
            startAutoStorageImport(space_id)


def disableContinuousImport(space_id):
    Logger.log(4, "disableContinuousImport(%s):" % space_id)
    if getContinuousImportStatus(space_id):
        result = setContinuousImport(space_id, False)
        if result:
            Logger.log(
                3, "Continuous import disabled for space with ID %s" % space_id, space_id=space_id
            )
            dareg.log(space_id, "info", "continuous scan disabled")
            time.sleep(1 * Settings.get().config["sleepFactor"])
            # continous import is disabled now
            # force (full) import of files last time
            startAutoStorageImport(space_id)

            # not doing anymore in filesystem due to variety options
            # permissions of all dirs and file should set to given permissions
            # mount_point = get_space_mount_point(space_id)
            # filesystem.chmod_recursive(mount_point, Settings.get().config["initialPOSIXlikePermissions"])

            posix_mode_string = oct(Settings.get().config["initialPOSIXlikePermissions"])
            if posix_mode_string.startswith("0o"):
                posix_mode_string = posix_mode_string[2:]

            file_id = get_space(space_id)["fileId"]
            files.setFileAttributeRecursive(
                file_id, posix_mode_string
            )

            # Set metadata for the space
            if Settings.get().config["importMetadata"]:
                metadata.setSpaceMetadataFromYaml(space_id)

            # set the space size to space occupancy
            setSpaceSize(space_id)


def getContinuousImportStatus(space_id):
    Logger.log(4, "getContinuousImportStatus(%s):" % space_id)
    space_details = getSpaceDetails(space_id)
    if space_details["importedStorage"]:
        return space_details["storageImport"]["autoStorageImportConfig"]["continuousScan"]
    else:
        Logger.log(
            2,
            "Imported storage value not available, space %s isn't imported" % space_id,
            space_id=space_id,
        )
        return None


def setContinuousImport(space_id, continuousScanEnabled):
    Logger.log(4, "setContinuousImport(%s, %s):" % (space_id, str(continuousScanEnabled)))
    autoStorageImportInfo = getAutoStorageImportInfo(space_id)["status"]
    # test if import was completed
    if (
            Settings.get().config["continousFileImport"]["enabled"]
            and autoStorageImportInfo == "completed"
    ):
        # https://onedata.org/#/home/api/21.02.0-alpha21/onepanel?anchor=operation/modify_space
        url = "onepanel/provider/spaces/" + space_id
        data = {
            "autoStorageImportConfig": {
                "continuousScan": continuousScanEnabled,
                "scanInterval": Settings.get().config["continousFileImport"]["scanInterval"],
                "detectModifications": Settings.get().config["continousFileImport"][
                    "detectModifications"
                ],
                "detectDeletions": Settings.get().config["continousFileImport"]["detectDeletions"],
            }
        }
        headers = dict({"Content-type": "application/json"})
        response = request.patch(url, headers=headers, data=json.dumps(data))
        if response.ok:
            return True
    else:
        Logger.log(
            2, "Continuous scan can't be changed for the space %s" % space_id, space_id=space_id
        )
        if autoStorageImportInfo != "completed":
            Logger.log(2, "Import of files is not completed yet", space_id=space_id)
        return False


def listSpaceGroups(space_id):
    Logger.log(4, "listSpaceGroups(%s):" % space_id)
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/list_space_groups
    url = "onezone/spaces/" + space_id + "/groups"
    response = request.get(url)
    return response.json()["groups"]


def addGroupToSpace(space_id, gid, privileges=None):
    """
    Add given group to the space. The third argument is list of the privileges,
    which the group will be given on the space.
    If no privileges are given, default privileges are used.
    """
    Logger.log(4, "addGroupToSpace(%s, %s, %s):" % (space_id, gid, privileges))
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/add_group_to_space
    url = "onezone/spaces/" + space_id + "/groups/" + gid
    headers = dict({"Content-type": "application/json"})
    data = {"privileges": privileges}
    response = request.put(url, headers=headers, data=json.dumps(data))
    if response.ok:
        Logger.log(
            3, "Space %s was added as member of group %s" % (space_id, gid), space_id=space_id
        )
        return response
    else:
        Logger.log(
            1, "Space %s wasn't added as member of group %s" % (space_id, gid), space_id=space_id
        )
        return response
