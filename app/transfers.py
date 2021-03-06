import json
from settings import Settings
from utils import Logger
import request

def getTransferStatus(transfer_id):
    Logger.log(4, "getTransferStatus(%s):" % transfer_id)
    # https://onedata.org/#/home/api/stable/oneprovider
    url = "oneprovider/transfers/" + transfer_id
    response = request.get(url)
    return response.json()

def createTransfer(replicating_provider_id, file_id):
    Logger.log(4, "createTransfer(%s, %s):" % (replicating_provider_id, file_id))
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/create_transfer
    url = "oneprovider/transfers"
    data = {
        "type": "replication",
        "replicatingProviderId": replicating_provider_id,
        "dataSourceType": "file",
        "fileId": file_id
    }

    headers = dict({'Content-type': 'application/json'})
    response = request.post(url, headers=headers, data=json.dumps(data))
    if response.ok:
        return response.json()
    else:
        return response

def getFileDistribution(file_id):
    Logger.log(4, "getFileDistribution(%s):" % file_id)
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=tag/File-Distribution
    url = "oneprovider/data/" + file_id + "/distribution"
    response = request.get(url)
    return response.json()
