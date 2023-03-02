import tokens
import groups
import storages
import spaces
import time
from utils import Settings
from utils import Logger


def action_space(space_name: str, space_id: str) -> bool:
    """
    Reverses steps of creating the space. Removing it.
    If name used when finding the space, first space which starts with ``space_name`` will be deleted.
    :param space_name: name of created space
    :param space_id: id of created space
    :return: True if successful, otherwise False
    """
    Logger.log(3, f"rollback - removing space with name {space_name} and id {space_id}")

    if not space_name and not space_id:
        Logger.log(1, f"rollback - no space name nor space id was provided")
        return False

    space = None

    Logger.log(3, f"rollback - getting space from id {space_id}")
    if space_id:
        space = spaces.get_space_from_onezone(space_id)  # space got, no need to change space id

    if not space:
        Logger.log(3, f"rollback - id is not correct, getting from name {space_name}")
        space_id = spaces.get_space_id_by_name(space_name)

        # it is ok, because we do not have to delete space
        if not space_id:
            Logger.log(3, "rollback - space does not exist on server, everything is OK")
            return True

    Logger.log(3, f"rollback - removing space with id {space_id}")
    response = spaces.removeSpace(space_id)
    Logger.log(3, f"rollback - space with id {space_id} removed: {response.ok}")

    time.sleep(2 * Settings.get().config["sleepFactor"])
    return response.ok


def action_storage(storage_name: str, storage_id: str) -> bool:
    """
    Reverses steps of creating the storage. Removing it.
    If name used when finding the storage, first storage which starts with ``storage_name`` will be deleted.
    :param storage_name: name of created storage
    :param storage_id: id of created storage
    :return: True if successful, otherwise False
    """
    Logger.log(3, f"rollback - removing storage with name {storage_name} and id {storage_id}")
    time.sleep(4 * Settings.get().config["sleepFactor"])

    if not storage_name and not storage_id:
        Logger.log(1, f"rollback - no storage name nor storage id was provided")
        return False

    storage = None

    Logger.log(3, f"rollback - getting storage from id {storage_id}")
    if storage_id:
        storage = storages.getStorageDetails(storage_id)  # storage got, no need to change storage id

    if not storage:
        Logger.log(3, f"rollback - id is not correct, getting from name {storage_name}")
        storage_id = storages.get_storage_id_by_name(storage_name)

        # it is ok, because we do not have to delete storage
        if not storage_id:
            Logger.log(3, "rollback - storage does not exist on server, everything is OK")
            return True

    Logger.log(3, f"rollback - removing storage with id {storage_id}")
    response = storages.removeStorage(storage_id)
    Logger.log(3, f"rollback - storage with id {storage_id} removed: {response.ok}")

    time.sleep(2 * Settings.get().config["sleepFactor"])
    return response.ok


def action_group(group_name: str, group_id: str):
    """
    Reverses steps of creating the group. Removing it.
    If name used when finding the group, first group which starts with ``group_name`` will be deleted.
    :param group_name: name of created group
    :param group_id: id of created group
    :return: True if successful, otherwise False
    """
    Logger.log(3, f"rollback - removing group with name {group_name} and id {group_id}")

    if not group_name and not group_id:
        Logger.log(1, f"rollback - no group name nor group id was provided")
        return False

    group = None

    Logger.log(3, f"rollback - getting group from id {group_id}")
    if group_id:
        group = groups.getGroupDetails(group_id)  # group got, no need to change group id

    if not group:
        Logger.log(3, f"rollback - id is not correct, getting from name {group_name}")
        group_id = groups.get_group_id_by_name(group_name)

        # it is ok, because we do not have to delete group
        if not group_id:
            Logger.log(3, "rollback - group does not exist on server, everything is OK")
            return True

    Logger.log(3, f"rollback - removing group with id {group_id}")
    response = groups.removeGroup(group_id)
    Logger.log(3, f"rollback - group with id {group_id} removed: {response.ok}")

    time.sleep(2 * Settings.get().config["sleepFactor"])
    return response.ok


def action_token(token_name: str, token_id: str) -> bool:
    """
    Reverses steps of creating the token. Removing it.
    :param token_name: name of created token
    :param token_id: id of created token
    :return: True if successful, otherwise False
    """
    Logger.log(3, f"rollback - removing token with name {token_name} and id {token_id}")

    if not token_name and not token_id:
        Logger.log(1, f"rollback - no token name nor token id was provided")
        return False

    token = None

    Logger.log(3, f"rollback - getting token from id {token_id}")
    if token_id:
        token = tokens.getNamedToken(token_id)  # token got, no need to change token id

    if not token:
        Logger.log(3, f"rollback - id is not correct, getting from name {token_name}")
        response = tokens.getNamedTokenByName(token_name)

        # it is ok, because we do not have to delete token
        if response.status_code == 404:
            Logger.log(3, "rollback - token does not exist on server, everything is OK")
            return True

        # TODO response moze dat aj iny status code, crash chance
        token_id = response["id"]

    Logger.log(3, f"rollback - removing token with id {token_id}")
    response = tokens.deleteNamedToken(token_id)
    Logger.log(3, f"rollback - token with id {token_id} removed: {response.ok}")

    time.sleep(2 * Settings.get().config["sleepFactor"])
    return response.ok
