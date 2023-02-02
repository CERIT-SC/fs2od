import request
from utils import Logger
import json

def add_requirement(file_id: str, expression: str, replicas_number: int) -> dict:
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

def get_all_requirements(file_id: str) -> dict:
    Logger.log(4, "get_all_qos_requirements_of_file(%s):" % file_id)
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/get_file_qos_summary
    url = "oneprovider/data/" + file_id + "/qos_summary"
    resp = request.get(url)

    return resp.json()["requirements"]


def delete_requirement(requirement_id: str) -> bool:
    Logger.log(4, "delete_requirement(%s):" % requirement_id)
    # https://onedata.org/#/home/api/stable/oneprovider?anchor=operation/remove_qos_requirement
    url = "oneprovider/qos-requirements/" + requirement_id
    resp = request.delete(url)

    return resp.status_code == 204


def delete_all_requirements_of_file(file_id: str) -> bool:
    Logger.log(4, "delete_all_requirements(%s):" % file_id)
    requirements = get_all_requirements(file_id)

    success = True

    for key, value in requirements.items():
        # if some value will be False, whole success will be False
        success &= delete_requirement(key)

    return success