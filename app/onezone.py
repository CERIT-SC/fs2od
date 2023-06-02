from settings import Settings
from utils import Logger, Utils
import request


def getConfiguration():
    Logger.log(4, "getConfiguration():")
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/get_configuration
    url = "onezone/configuration"
    response = request.get(url)
    return response.json()


def getCurrentUserDetails():
    Logger.log(4, "getCurrentUserDetails():")
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/get_current_user
    url = "onezone/user"
    response = request.get(url)
    if not response.ok:
        Logger.log(1, "Current user details can't be retrieved")

    return response.json()


def get_all_providers_of_onezone() -> list:
    Logger.log(4, "get_all_providers_of_onezone()")
    # https://onedata.org/#/home/api/21.02.1/onezone?anchor=tag/Provider
    url = "onezone/providers/"
    response = request.get(url)
    if not response.ok:
        Logger.log(1, "Providers of Onezone cannot be retrieved")
        return []

    response_json = response.json()

    if "providers" not in response_json:
        Logger.log(2, "Response ok, but providers not retrieved")
        return []

    return response_json["providers"]


def get_provider_details_from_onezone(provider_id: str) -> dict:
    Logger.log(4, f"get_provider_details_from_onezone(pr_id={provider_id})")
    # https://onedata.org/#/home/api/21.02.1/onezone?anchor=operation/get_provider_details
    url = "onezone/providers/" + provider_id
    response = request.get(url)

    if not response.ok:
        Logger.log(1, f"Information about provider with id {provider_id} cannot be retrieved")
        return {}

    response_json = response.json()

    if not response_json or "providerId" not in response_json:
        Logger.log(2, "Response ok, but information not retrieved")

    return response_json


def get_providers_supported_spaces_from_onezone(provider_id: str) -> list:
    Logger.log(4, f"get_providers_supported_spaces_from_onezone(pr_id={provider_id})")
    # https://onedata.org/#/home/api/stable/onezone?anchor=operation/list_provider_supported_spaces
    url = "onezone/providers/" + provider_id + "/spaces"
    response = request.get(url)

    if not response.ok:
        Logger.log(1, f"Spaces for provider with id {provider_id} cannot be retrieved")
        return []

    response_json = response.json()

    if not response_json or "spaces" not in response_json:
        Logger.log(2, "Response ok, but spaces information not retrieved")

    return response_json["spaces"]


def resolve_provider_id_from_id_or_hostname(id_or_hostname: str) -> str:
    Logger.log(4, f"resolve_provider_id_from_id_or_hostname(id_or_host={id_or_hostname})")

    provider_ids = get_all_providers_of_onezone()

    # we got correct provider_id
    if id_or_hostname in provider_ids:
        return id_or_hostname

    for provider_id in provider_ids:
        provider_details = get_provider_details_from_onezone(provider_id)
        if not provider_details:
            continue

        provider_domain = provider_details["domain"]

        if Utils.is_host_name_the_same(provider_domain, id_or_hostname):
            return provider_id

    return ""
