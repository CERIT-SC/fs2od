import json
from settings import Settings
from utils import Logger
import request


def get_transfer_status(transfer_id: str, status_type_if_not_found: str = "transferStatus") -> dict:
    """
    Returns transfer info for given transfer id.
    If transfer was not found, it is considered as completed and removed further by Onedata.
    If that happens, status which is checked (provided in variable status_type_if_not_found) is set to value "not_found"
    Any other error returns empty dict
    >>> # possible usage - after transfer creation, having transfer id, transfer type was set to replication
    >>> status = get_transfer_status(transfer_id, "replicationStatus")
    >>> if not status: # internal error, not sufficient rights
    >>>     # do stuff
    >>> if status["replicationStatus"] == "not_found":
    >>>     # you know that it is not present, do stuff
    >>> status = status["replicationStatus"] # now can be anything from documentation
    """
    Logger.log(4, "getTransferStatus(%s):" % transfer_id)
    # https://onedata.org/#/home/api/stable/oneprovider
    url = "oneprovider/transfers/" + transfer_id
    response = request.get(url, ok_statuses=(200, 404))

    if response.ok:
        return response.json()
    elif response.status_code == 404:
        return {status_type_if_not_found: "not_found"}
    else:
        return {}


# WIP
def createTransfer(type, replicating_provider_id, file_id, dataSourceType) -> dict:
    Logger.log(
        4,
        "createTransfer(%s, %s, %s, %s):"
        % (type, replicating_provider_id, file_id, dataSourceType),
    )
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/create_transfer
    url = "oneprovider/transfers"
    data = {
        "type": type,
        "replicatingProviderId": replicating_provider_id,
        "dataSourceType": dataSourceType,
        "fileId": file_id,
    }

    headers = dict({"Content-type": "application/json"})
    response = request.post(url, headers=headers, data=json.dumps(data))
    if response.ok:
        return response.json()
    else:
        return {}


# WIP
def createReplicationTransfer(replicating_provider_id, file_id, dataSourceType="file"):
    createTransfer("replication", replicating_provider_id, file_id, dataSourceType)


def getFileDistribution(file_id):
    Logger.log(4, "getFileDistribution(%s):" % file_id)
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=tag/File-Distribution
    url = "oneprovider/data/" + file_id + "/distribution"
    response = request.get(url)
    return response.json()
