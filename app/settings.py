from __future__ import annotations
import datetime
import os
import sys
from typing import Union, List
import ruamel.yaml
from urllib.parse import urlparse


class Messaging:
    class EmailCreds:
        def __init__(self):
            self.enabled: bool = False
            self.smtp_server: str = ""
            self.smtp_port: int = 0
            self.login: str = ""
            self.password: str = ""
            self.encryption_method: str = ""
            self.message_sender: str = ""

    class Email:
        def __init__(self):
            self.to: dict = {}
            self.time_before_action: List[datetime.timedelta] = []
            self.language: str = ""

    def __init__(self):
        self.email_creds: Messaging.EmailCreds = self.EmailCreds()
        self.email: Messaging.Email = self.Email()

    @staticmethod
    def create(config: dict) -> Messaging:
        messaging = Messaging()
        email_credentials_config = config["messaging"]["credentials"]["email"]
        email_config = config["messaging"]["email"]
        messaging.email_creds.enabled = email_credentials_config["enabled"]

        if messaging.email_creds.enabled:
            messaging.email_creds.smtp_server = email_credentials_config["smtpServer"]
            messaging.email_creds.smtp_port = email_credentials_config["smtpPort"]
            messaging.email_creds.login = email_credentials_config["login"]
            messaging.email_creds.password = email_credentials_config["password"]
            messaging.email_creds.encryption_method = email_credentials_config["encryptionMethod"]
            messaging.email_creds.message_sender = email_credentials_config["messageSender"]

            messaging.email.to = email_config["to"]
            messaging.email.time_before_action = email_config["timeBeforeAction"]
            messaging.email.time_before_action.sort(reverse=True)

            lang = email_config["language"].lower()
            # default language is en, so if this language is used, file has no other extension (filename.extension)
            # if there is some translation of document, filename will be filename.lang.extension
            lang = "" if lang == "en" else f".{lang}"
            messaging.email.language = lang

        return messaging


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
        self.debug: int = 5
        self.TEST: bool = False
        self.TEST_PREFIX: str = ""
        self.METADATA_FILES: List[str] = []
        self.ONEZONE_HOST: str = ""
        self.ONEZONE_API_KEY: str = ""
        self.MAIN_ONEPROVIDER_HOST: str = ""
        self.MAIN_ONEPROVIDER_API_KEY: str = ""
        self.ONEZONE_API_URL: str = ""
        self.ONEPROVIDER_API_URL: str = ""
        self.ONEPROVIDERS_API_URL: List[str] = []
        self.ONEPROVIDERS_DOMAIN_NAMES: List[str] = []
        self.ONEZONE_AUTH_HEADERS: dict[str, str] = {}
        self.ONEPROVIDER_AUTH_HEADERS: dict[str, str] = {}
        self.ONEPROVIDERS_AUTH_HEADERS: List[dict] = []
        self.ONEPROVIDERS_STORAGE_IDS: List[List[str]] = []
        self.DATA_REPLICATION_ENABLED: bool = False
        self.DATA_REPLICATION_REPLICAS: int = 0
        self.DAREG_ENABLED: bool = False
        self.MIN_ONEDATA_NAME_LENGTH: int = 2
        self.MAX_ONEDATA_NAME_LENGTH: int = 50
        self.TIME_UNTIL_REMOVED: str = "never"
        self.TIME_FORMATTING_STRING: str = "%d. %m. %Y %H:%M"
        self.REMOVE_FROM_FILESYSTEM: bool = False
        self.MESSAGING: Messaging = Messaging()
        self.USE_SEPARATE_METADATA_FILE: bool = False
        self.SEPARATE_METADATA_FILENAME: str = ""
        self.SEPARATE_METADATA_STORE_ACCESS: bool = True
        if Settings.__instance is not None:
            raise Exception(
                "This class is a singleton! Created once, otherwise use Settings.get_instance()"
            )
        else:
            self.setup(config)
            Settings.__instance = self

    @staticmethod
    def get() -> Settings:
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
        if not os.path.exists(config_file):
            print("[Error] config file %s doesn't exists" % config_file)
            sys.exit(1)
        with open(config_file, "r") as stream:
            try:
                yaml = ruamel.yaml.YAML(typ="safe")
                self.config = yaml.load(stream)
            except Exception as e:
                print("[Error] exception occured during loading config file", config_file)
                print(str(e))
                sys.exit(1)

        self.check_configuration()

        self.debug: bool = self.config["verboseLevel"]

        self.TEST: bool = self.config["testMode"]
        self.TEST_PREFIX: str = self.config["testModePrefix"]

        self.METADATA_FILES: List[str] = self.config["metadataFiles"]

        # Setup the access Onedata variables
        self.ONEZONE_HOST: str = self.config["restAccess"]["onezone"]["host"]
        self.ONEZONE_API_KEY: str = self.config["restAccess"]["onezone"]["apiToken"]

        providers: list = self.config["restAccess"]["oneproviders"]
        for provider_index in range(len(providers)):
            if providers[provider_index]["isPrimary"]:
                self.MAIN_ONEPROVIDER_HOST: str = providers[provider_index]["host"]
                self.MAIN_ONEPROVIDER_API_KEY: str = providers[provider_index]["apiToken"]

                # now we have the certainty that when iterating through providers,
                # we will not access main provider
                providers.pop(provider_index)
                break

        self.ONEZONE_API_URL: str = self.ONEZONE_HOST + "/api/v3/"
        self.ONEPROVIDER_API_URL: str = self.MAIN_ONEPROVIDER_HOST + "/api/v3/"
        self.ONEPROVIDERS_API_URL: list[str] = [self.ONEPROVIDER_API_URL] + [
            provider["host"] + "/api/v3/"
            for provider in self.config["restAccess"]["oneproviders"]
        ]

        self.ONEPROVIDERS_DOMAIN_NAMES: list[str] = [
            self._get_domain_name_from_url(api_url) for api_url in self.ONEPROVIDERS_API_URL
        ]

        self.ONEZONE_AUTH_HEADERS: dict[str, str] = {"x-auth-token": self.ONEZONE_API_KEY}
        self.ONEPROVIDER_AUTH_HEADERS: dict[str, str] = {"x-auth-token": self.MAIN_ONEPROVIDER_API_KEY}

        # all authentication headers for oneproviders in one place
        self.ONEPROVIDERS_AUTH_HEADERS: List[dict] = [self.ONEPROVIDER_AUTH_HEADERS] + [
            {"x-auth-token": provider["apiToken"]}
            for provider in self.config["restAccess"]["oneproviders"]
        ]

        self.ONEPROVIDERS_STORAGE_IDS: List[List[str]] = [[]] + [
            provider["storageIds"] for provider in providers
        ]

        self.DATA_REPLICATION_ENABLED: bool = self.config["dataReplication"]["enabled"]
        self.DATA_REPLICATION_REPLICAS: int = self.config["dataReplication"]["numberOfReplicas"]
        self.DAREG_ENABLED: bool = self.config["dareg"]["enabled"]

        # Onedata name must be 2-50 characters long
        self.MIN_ONEDATA_NAME_LENGTH = 2
        self.MAX_ONEDATA_NAME_LENGTH = 50

        self.TIME_UNTIL_REMOVED: str = self.config["dataReplication"]["timeUntilRemoved"]
        self.TIME_FORMATTING_STRING = "%d. %m. %Y %H:%M"
        self.REMOVE_FROM_FILESYSTEM: bool = self.config["dataReplication"]["removeFromFilesystem"]

        self.MESSAGING: Messaging = Messaging.create(self.config)

        self.USE_SEPARATE_METADATA_FILE: bool = self.config["fs2odMetadataFile"]["enabled"]
        self.SEPARATE_METADATA_FILENAME: str = self.config["fs2odMetadataFile"]["filename"]
        self.SEPARATE_METADATA_STORE_ACCESS: bool = self.config["fs2odMetadataFile"]["storeAccessInfo"]
        if not self.USE_SEPARATE_METADATA_FILE:
            self.SEPARATE_METADATA_STORE_ACCESS = False

    @staticmethod
    def _failed(message):
        print("[Error] %s" % message)
        sys.exit(1)

    @staticmethod
    def _info(message: str) -> None:
        print(f"[Info] {message}")

    @staticmethod
    def _test_existence(dictionary, attribute, default=None, parent_name: str = "") -> bool:
        """
        Tests existence of a value.
        If default value not provided and value not present, exits application.
        Returns False if default value was used, otherwise True
        """
        message_about_parent = ""
        if parent_name:
            message_about_parent = f" for {parent_name}"

        if attribute not in dictionary:
            if default is None:
                print(f"[Error] attribute {attribute} not set in configuration file{message_about_parent}")
                sys.exit(1)
            else:
                dictionary[attribute] = default
                if not type(attribute) is dict:
                    Settings._info(
                        f"no attribute {attribute}{message_about_parent}"
                        f" in configuration file, using its default value [{default}]"
                    )
                    return False

        return True

    @staticmethod
    def _test_if_empty(dictionary, attribute, default=None, parent_name: str = "") -> bool:
        """
        Tests if value is not empty.
        If default value not provided and value empty, exits application.
        Returns False if default value was used, otherwise True
        """
        if type(dictionary[attribute]) in (int, bool, float):
            return True
        message_about_parent = ""
        if parent_name:
            message_about_parent = f" for {parent_name}"

        if not dictionary[attribute]:
            if default is None:
                print(f"[Error] attribute {attribute} is empty{message_about_parent}")
                sys.exit(1)
            else:
                dictionary[attribute] = default

                Settings._info(
                    f"attribute {attribute} is empty{message_about_parent}, using default value [{default}]"
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

    @staticmethod
    def _get_domain_name_from_url(url: str) -> str:
        """
        Returns pure domain name.
        """
        host_object = urlparse(url)

        return host_object.netloc

    @staticmethod
    def _convert_time_string_to_datetime(time_string: str) -> Union[datetime.timedelta, str]:
        if not time_string:
            return "never"
        if time_string == "never" or time_string == "now":
            return time_string

        error_count = 0
        years = 0
        months = 0
        days = 0
        hours = 0

        times = time_string.split()

        for time in times:
            time_type = time[-1]
            time = time[:-1]

            try:
                time_int = int(time)
            except ValueError:
                error_count += 1
            else:
                if time_type == "y":
                    years += time_int
                elif time_type == "m":
                    months += time_int
                elif time_type == "d":
                    days += time_int
                elif time_type == "h":
                    hours += time_int

        days += years * 365
        days += months * 30

        if (days + hours) == 0 and error_count:
            return "never"

        return datetime.timedelta(days=days, hours=hours)

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
        self._test_existence(self.config["metadataFileTags"], "onezone", "Onezone")
        self._test_existence(self.config["metadataFileTags"], "space", "Space")
        self._test_existence(self.config["metadataFileTags"], "publicURL", "PublicURL")
        self._test_existence(self.config["metadataFileTags"], "inviteToken", "InviteToken")
        self._test_existence(self.config["metadataFileTags"], "deniedProviders", "DeniedProviders")
        self._test_existence(self.config["metadataFileTags"], "removingTime", "RemovingTime")
        self._test_existence(self.config["metadataFileTags"], "lastProgramRun", "LastProgramRun")

        self._test_existence(self.config, "fs2odMetadataFile", dict())
        self._test_existence(self.config["fs2odMetadataFile"], "enabled", False, parent_name="fs2odMetadataFile")
        self._test_existence(self.config["fs2odMetadataFile"], "filename", ".fs2od", parent_name="fs2odMetadataFile")
        self._test_if_empty(self.config["fs2odMetadataFile"], "filename", parent_name="fs2odMetadataFile")
        self._test_existence(self.config["fs2odMetadataFile"], "storeAccessInfo", True, parent_name="fs2odMetadataFile")

        self._test_existence(self.config, "institutionName")
        self._test_existence(self.config, "datasetPrefix", "")
        self._test_existence(self.config, "importMetadata", True)
        self._test_existence(self.config, "parseMetadataToShare", False)

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
        self.config["initialPOSIXlikePermissions"] = int(self.config["initialPOSIXlikePermissions"], 8)
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

        self._test_existence(self.config, "restAccess")
        self._test_existence(self.config["restAccess"], "onezone")
        self._test_existence(self.config["restAccess"]["onezone"], "host", parent_name="onezone")
        self._test_if_empty(self.config["restAccess"]["onezone"], "host", parent_name="onezone")
        # test if http/s
        self.config["restAccess"]["onezone"]["host"] = self._add_protocol_to_host_if_missing(
            self.config["restAccess"]["onezone"]["host"]
        )
        self._test_existence(self.config["restAccess"]["onezone"], "apiToken")

        self._test_existence(self.config["restAccess"], "oneproviders")
        self._test_if_empty(self.config["restAccess"], "oneproviders")

        have_primary_provider = False
        for key, provider in enumerate(self.config["restAccess"]["oneproviders"]):
            self._test_existence(provider, "host", parent_name=f"oneprovider {key}")
            self._test_if_empty(provider, "host", parent_name=f"oneprovider {key}")
            # test if http/s
            provider["host"] = self._add_protocol_to_host_if_missing(provider["host"])
            self._test_existence(provider, "apiToken", parent_name=f"oneprovider {key}")
            self._test_if_empty(provider, "apiToken", parent_name=f"oneprovider {key}")

            this_is_primary = self._test_existence(provider, "isPrimary", False, parent_name=f"oneprovider {key}")
            if not this_is_primary:
                self._test_existence(provider, "storageIds", parent_name=f"oneprovider {key}")
                self._test_if_empty(provider, "storageIds", parent_name=f"oneprovider {key}")
                for storage_index in range(len(provider["storageIds"])):
                    self._test_if_empty(provider["storageIds"], storage_index, parent_name=f"oneprovider {key}")
            else:
                if have_primary_provider:
                    self._failed("more primary providers set, program can have only one")

                have_primary_provider = True

        if not have_primary_provider:
            self._failed("primary provider not provided")

        self._test_existence(self.config["dataReplication"], "numberOfReplicas", 1)
        self._test_existence(self.config["dataReplication"], "timeUntilRemoved", "never")
        self.config["dataReplication"]["timeUntilRemoved"] = self._convert_time_string_to_datetime(
            self.config["dataReplication"]["timeUntilRemoved"])
        self._test_existence(self.config["dataReplication"], "removeFromFilesystem", False)

        number_of_providers = len(self.config["restAccess"]["oneproviders"])
        number_of_replicas = self.config["dataReplication"]["numberOfReplicas"]
        if number_of_replicas > number_of_providers:
            self._info(f"Number of replicas is higher than number of providers "
                       f"({number_of_replicas} > {number_of_providers}). Decreasing to maximum possible.")
            self.config["dataReplication"]["numberOfReplicas"] = number_of_providers

        self._test_existence(self.config, "messaging", dict())
        self._test_existence(self.config["messaging"], "credentials", dict())
        self._test_existence(self.config["messaging"], "email", dict())
        self._test_existence(self.config["messaging"]["credentials"], "email", dict())

        if self._test_existence(self.config["messaging"]["credentials"]["email"], "enabled", False) and \
                self.config["messaging"]["credentials"]["email"]["enabled"] is True:
            email_creds = self.config["messaging"]["credentials"]["email"]

            self._test_existence(email_creds, "smtpServer")
            self._test_if_empty(email_creds, "smtpServer")

            self._test_existence(email_creds, "encryptionMethod")
            if email_creds["encryptionMethod"] not in ("SSL", "TLS", "STRATTLS", "ANY"):
                self._failed("Encryption method for email is not correct")

            self._test_existence(email_creds, "smtpPort")
            self._test_if_empty(email_creds, "smtpPort", 0)
            if type(email_creds["smtpPort"]) != int:
                self._failed("Port for email is not correct")
            if email_creds["smtpPort"] == 0:
                email_creds["smtpPort"] = 465 if email_creds["encryptionMethod"] in ("SSL", "TLS") else email_creds["smtpPort"]
                email_creds["smtpPort"] = 587 if email_creds["encryptionMethod"] == "STARTTLS" else email_creds["smtpPort"]
                email_creds["smtpPort"] = 25 if email_creds["encryptionMethod"] == "ANY" else email_creds["smtpPort"]

            self._test_if_empty(email_creds, "login", "")
            self._test_if_empty(email_creds, "password", "")
            if not email_creds["login"] or not email_creds["password"]:
                email_creds["login"] = ""
                email_creds["password"] = ""
            self._test_if_empty(email_creds, "messageSender", "")

            self._test_existence(self.config["messaging"]["email"], "to", default={}, parent_name="email")
            self._test_existence(
                self.config["messaging"]["email"]["to"], "space_creation", parent_name="email->to")
            self._test_existence(
                self.config["messaging"]["email"]["to"], "space_deletion", parent_name="email->to")
            self._test_existence(self.config["messaging"]["email"], "timeBeforeAction", list())

            time_before_action = self.config["messaging"]["email"]["timeBeforeAction"]
            time_delta_before_action = []
            for key, time_str in enumerate(time_before_action):
                converted = self._convert_time_string_to_datetime(time_str)
                if type(converted) == datetime.timedelta:
                    time_delta_before_action.append(converted)

            self.config["messaging"]["email"]["timeBeforeAction"] = time_delta_before_action

            self._test_existence(self.config["messaging"]["email"], "language", "EN")
