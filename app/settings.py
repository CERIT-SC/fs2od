import os
import sys
import ruamel.yaml
from urllib.parse import urlparse


class Settings:
    """
    Singleton class to serve the global configuration.
    """

    __instance = None
    config = None

    def __init__(self, config):
        """
        Virtually private constructor.
        """
        if Settings.__instance != None:
            raise Exception(
                "This class is a singleton! Created once, otherwise use Settings.get_instance()"
            )
        else:
            self.setup(config)
            Settings.__instance = self

    @staticmethod
    def get():
        """
        Static access method, return instance of Settings or instantiate it.
        """
        if Settings.__instance == None:
            Settings()
        return Settings.__instance

    def setup(self, config_file):
        """
        Load configuration from given YAML file.
        """
        if os.path.exists(config_file):
            with open(config_file, "r") as stream:
                try:
                    yaml = ruamel.yaml.YAML(typ="safe")
                    self.config = yaml.load(stream)
                except Exception as e:
                    print("[Error] exception occured during loading config file", config_file)
                    print(str(e))
                    sys.exit(1)

                self.check_configuration()

                self.debug = self.config["verboseLevel"]

                self.TEST = self.config["testMode"]
                self.TEST_PREFIX = self.config["testModePrefix"]

                # Setup the access Onedata variables
                self.ONEZONE_HOST = self.config["onezone"]["host"]
                self.ONEZONE_API_KEY = self.config["onezone"]["apiToken"]

                self.ONEPROVIDER_HOST = self.config["oneprovider"]["host"]
                self.ONEPROVIDER_API_KEY = self.config["oneprovider"]["apiToken"]

                self.ONEPANEL_HOST = self.config["onepanel"]["host"]
                self.ONEPANEL_API_KEY = self.config["onepanel"]["apiToken"]

                self.ONEZONE_API_URL = self.ONEZONE_HOST + "/api/v3/"
                self.ONEPROVIDER_API_URL: str = self.ONEPROVIDER_HOST + "/api/v3/"
                self.ONEPROVIDERS_API_URL: list = [self.ONEPROVIDER_API_URL] + [
                    provider["host"] + "/api/v3/"
                    for provider in self.config["dataReplication"]["supportingProviders"]
                ]
                self.ONEPANEL_API_URL = self.ONEPANEL_HOST + "/api/v3/"

                self.ONEZONE_AUTH_HEADERS = {"x-auth-token": self.ONEZONE_API_KEY}
                self.ONEPROVIDER_AUTH_HEADERS: dict = {"x-auth-token": self.ONEPROVIDER_API_KEY}

                # all authentication headers for oneproviders in one place
                self.ONEPROVIDERS_AUTH_HEADERS: list = [self.ONEPROVIDER_AUTH_HEADERS] + [
                    {"x-auth-token": provider["apiToken"]}
                    for provider in self.config["dataReplication"]["supportingProviders"]
                ]
                self.ONEPANEL_AUTH_HEADERS = {"x-auth-token": self.ONEPANEL_API_KEY}

                self.ONEPANELS_AUTH_HEADERS: list = [self.ONEPANEL_AUTH_HEADERS] + [
                    {"x-auth-token": provider["onepanelApiToken"]}
                    for provider in self.config["dataReplication"]["supportingProviders"]
                ]

                self.DATA_REPLICATION_ENABLED: bool = self.config["dataReplication"]["enabled"]
                self.DATA_REPLICATION_REPLICAS: bool = self.config["dataReplication"]["numberOfReplicas"]
                self.DAREG_ENABLED: bool = self.config["dareg"]["enabled"]

                # Onedata name must be 2-50 characters long
                self.MIN_ONEDATA_NAME_LENGTH = 2
                self.MAX_ONEDATA_NAME_LENGTH = 50
        else:
            print("[Error] config file %s doesn't exists" % config_file)
            sys.exit(1)

    @staticmethod
    def _failed(message):
        print("[Error] %s" % message)
        sys.exit(1)

    @staticmethod
    def _info(message: str) -> None:
        print(f"[Info] {message}")

    @staticmethod
    def _test_existence(dictionary, attribute, default=None) -> bool:
        """
        Tests existence of a value.
        If default value not provided and value not present, exits application.
        Returns False if default value was used, otherwise True
        """
        if attribute not in dictionary:
            if default is None:
                print("[Error] attribute %s not set in configuration file" % attribute)
                sys.exit(1)
            else:
                dictionary[attribute] = default
                if not type(attribute) is dict:
                    Settings._info(
                        "no attribute %s in configuration file, using its default value [%s]"
                        % (attribute, default)
                    )
                    return False

        return True

    @staticmethod
    def _test_if_empty(dictionary, attribute, default=None) -> bool:
        """
        Tests if value is not empty.
        If default value not provided and value empty, exits application.
        Returns False if default value was used, otherwise True
        """
        if type(dictionary[attribute]) in (int, bool, float):
            return True

        if not dictionary[attribute]:
            if default is None:
                print(f"[Error] attribute {attribute} is empty")
                sys.exit(1)
            else:
                dictionary[attribute] = default

                Settings._info(
                    f"attribute {attribute} is empty, using default value [{default}]"
                    )
                return False

        return True

    @staticmethod
    def _add_protocol_to_host_if_missing(host: str, allowed_protocols: tuple = ("https", "http")) -> str:
        """
        Adds a protocol to the host url if missing. If no or not allowed protocol used, replaces with first available.
        """
        assert len(allowed_protocols) > 0, "There must be at least one allowed protocol"

        host_object = urlparse(host)
        # test actual protocol
        if host_object.scheme not in allowed_protocols:
            host_object = host_object._replace(scheme=allowed_protocols[0])
            # when protocol missing, it parses as path, not network address
            host_object = host_object._replace(netloc=host_object.path)
            host_object = host_object._replace(path="")

        # return to string
        host = host_object.geturl()

        return host

    def check_configuration(self):
        self._test_existence(self.config, "watchedDirectories")
        if (
            type(self.config["watchedDirectories"]) is not list
            or len(self.config["watchedDirectories"]) < 1
        ):
            self._failed("no watched directory defined in watchedDirectories")

        self._test_existence(self.config, "metadataFiles")
        if type(self.config["metadataFiles"]) is not list or len(self.config["metadataFiles"]) < 1:
            self._failed("no metadata file defined in metadataFiles")

        self._test_existence(self.config, "metadataFileTags", dict())
        self._test_existence(self.config["metadataFileTags"], "onedata", "Onedata")
        self._test_existence(self.config["metadataFileTags"], "space", "Space")
        self._test_existence(self.config["metadataFileTags"], "publicURL", "PublicURL")
        self._test_existence(self.config["metadataFileTags"], "inviteToken", "InviteToken")

        self._test_existence(self.config, "institutionName")
        self._test_existence(self.config, "datasetPrefix", "")
        self._test_existence(self.config, "importMetadata", True)

        self._test_existence(self.config, "verboseLevel", 3)
        self._test_existence(self.config, "testMode", False)
        self._test_existence(self.config, "testModePrefix", "test_fs2od")
        self._test_existence(self.config, "sleepFactor", 2)

        self._test_existence(self.config, "continousFileImport", dict())
        self._test_existence(self.config["continousFileImport"], "enabled", True)
        self._test_existence(self.config["continousFileImport"], "runningFileName", ".running")
        self._test_existence(self.config["continousFileImport"], "scanInterval", 10800)
        self._test_existence(self.config["continousFileImport"], "detectModifications", False)
        self._test_existence(self.config["continousFileImport"], "detectDeletions", False)
        self._test_existence(self.config["continousFileImport"], "enabled", True)

        self._test_existence(self.config, "initialPOSIXlikePermissions", "0775")
        self._test_existence(self.config, "userGroupId")
        self._test_existence(self.config, "implicitSpaceSize", 10995116277760)
        self._test_existence(self.config, "serviceUserId")
        self._test_existence(self.config, "managerGroupId")

        self._test_existence(self.config, "dareg", dict())
        self._test_existence(self.config["dareg"], "enabled", False)
        self._test_existence(self.config["dareg"], "host", "https://dareg.example.com")
        # test if http/s
        self.config["dareg"]["host"] = self._add_protocol_to_host_if_missing(self.config["dareg"]["host"])
        self._test_existence(self.config["dareg"], "token", "a_secret_token")
        self._test_existence(self.config["dareg"], "origin_instance_pk", 1)

        self._test_existence(self.config, "onezone")
        self._test_existence(self.config["onezone"], "host")
        # test if http/s
        self.config["onezone"]["host"] = self._add_protocol_to_host_if_missing(self.config["onezone"]["host"])
        self._test_existence(self.config["onezone"], "apiToken")
        self._test_existence(self.config, "oneprovider")
        self._test_existence(self.config["oneprovider"], "host")
        # test if http/s
        self.config["oneprovider"]["host"] = self._add_protocol_to_host_if_missing(self.config["oneprovider"]["host"])
        self._test_existence(self.config["oneprovider"], "apiToken")
        self._test_existence(self.config, "onepanel")
        self._test_existence(self.config["onepanel"], "host")
        # test if http/s
        self.config["onepanel"]["host"] = self._add_protocol_to_host_if_missing(self.config["onepanel"]["host"])
        self._test_existence(self.config["onepanel"], "apiToken")

        self._test_existence(self.config, "dataReplication", dict())
        self._test_existence(self.config["dataReplication"], "enabled", False)
        self._test_existence(self.config["dataReplication"], "managerSpaceId")
        # list of dicts
        self._test_existence(self.config["dataReplication"], "supportingProviders", list())
        # if there are supporters, they must have host and token
        for item in self.config["dataReplication"]["supportingProviders"]:
            self._test_existence(item, "host")
            # using python mutability and list referencing
            item["host"] = self._add_protocol_to_host_if_missing(item["host"])
            self._test_existence(item, "apiToken")
            self._test_existence(item, "onepanelApiToken")
            self._test_existence(item, "storageIds")

            if len(item["storageIds"]) == 0:
                self._failed("storage IDs not provided")
        self._test_existence(self.config["dataReplication"], "numberOfReplicas", 1)

        number_of_providers = len(self.config["dataReplication"]["supportingProviders"]) + 1
        number_of_replicas = self.config["dataReplication"]["numberOfReplicas"]
        if number_of_replicas > number_of_providers:
            self._info(f"Number of replicas is higher than number of providers "
                       f"({number_of_replicas} > {number_of_providers}). Decreasing to maximum possible.")
            self.config["dataReplication"]["numberOfReplicas"] = number_of_providers
