import request, spaces
from utils import Logger
import json
def add_qos_to_space(space_id: str, replicas_number: int) -> str:
    Logger.log(4, "add_qos_to_space(%s):" % space_id)
    space_info = spaces.getSpace(space_id)

    file_id = space_info["fileId"]

    response = add_qos_to_file(file_id, "anyStorage", replicas_number)

    return response["qosRequirementId"]

def add_qos_to_file(file_id: str, expression: str, replicas_number: int) -> dict:
    Logger.log(4, "add_qos_to_file(%s):" % file_id)
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/add_qos_requirement
    url = "oneprovider/qos_requirements"
    data = {
        "expression": expression,
        "replicasNum": replicas_number,
        "fileId": file_id
    }

    headers = dict({"Content-type": "application/json"})
    resp = request.post(url, headers=headers, data=json.dumps(data))

    return resp.json()

