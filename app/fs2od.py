#!/usr/bin/env python3

import argparse
import sys
from pprint import pprint
from settings import Settings
from utils import Logger
import filesystem
import test
import sandbox
import actions_log


def runScan(args):
    if not args.no_test_connection:
        result = test.testConnection(of_each_oneprovider=False)
        if result:
            sys.exit(1)

    # after successful connection there is need to check some forgotten log
    actions_log.get_actions_logger().new_actions_log()
    actions_log.get_actions_logger().finish_actions_log()

    if args.no_metadata_usage:
        Settings.get().USE_METADATA_FILE = False

    filesystem.scanWatchedDirectories()


def run_test_remove(args):
    test.remove(args)


def run_test_change(args):
    test.change(args)


def runTestRegisterSpace(args):
    test.registerSpace(args.register_space)


def runTestConnection(args):
    if args.ignore_disabled_status:
        test.testConnection(of_each_oneprovider=True)
    else:
        test.testConnection(of_each_oneprovider=False)


def runSandbox(args):
    sandbox.sandbox(args)


def runCheck(args):
    filesystem.scanWatchedDirectories(True)


def main():
    parser = argparse.ArgumentParser(description="FS2OD - Filesystem to Onedata importing software")
    parser.add_argument(
        "--config",
        default="config.yaml",
        required=False,
        type=str,
        help="Path to YAML configuration file (default value is ./config.yaml)",
    )
    subparsers = parser.add_subparsers(help="Name of workflow which will be run")

    parser_1 = subparsers.add_parser("scan", help="Scan watched directories and import to Onedata")
    parser_1.set_defaults(func=runScan)
    parser_1.add_argument(
        "--no-test-connection", required=False, action="store_true", help="If included, tests will not be performed"
    )
    parser_1.add_argument(
        "--no-metadata-usage", required=False, action="store_true",
        help="If included, metadata file (as .fs2od) is not used"
    )

    parser_2 = subparsers.add_parser("test", help="Do defined test workflow")
    subparser_2 = parser_2.add_subparsers(help="Name of test workflow which will be run")

    parser_2_1 = subparser_2.add_parser(
        "register_space", help="Register space - create space (storage, group, token)."
    )
    parser_2_1.add_argument("--path", required=True, type=str, help="Path to space")
    parser_2_1.set_defaults(func=runTestRegisterSpace)

    parser_2_2 = subparser_2.add_parser(
        "remove",
        help="Delete instances (storages, spaces, groups, tokens) with a given rule.",
    )
    parser_2_2.add_argument(
        "--all", required=False, action="store_true",
        help="Includes all instances (storages, spaces, groups, tokens)"
    )
    parser_2_2.add_argument(
        "--spaces", required=False, action="store_true",
        help="Include spaces"
    )
    parser_2_2.add_argument(
        "--storages", required=False, action="store_true",
        help="Include storages"
    )
    parser_2_2.add_argument(
        "--tokens", required=False, action="store_true",
        help="Include tokens"
    )
    parser_2_2.add_argument(
        "--groups", required=False, action="store_true",
        help="Include groups"
    )
    parser_2_2.add_argument(
        "--starting_with", required=False, default=None, type=str, metavar="NAME",
        help="Prefix of instances to remove (default is testModePrefix value from config file)"
    )
    parser_2_2.add_argument(
        "--of_provider", required=False, default="", type=str, metavar="PROVIDER",
        help="Provider of instances to remove"
    )
    parser_2_2.add_argument(
        "--with_more_providers", required=False, action="store_true",
        help="If set, removes instances also when they have more than one supporting provider. "
             "--of-provider must be used"
    )

    parser_2_2.set_defaults(func=run_test_remove)

    parser_2_3 = subparser_2.add_parser(
        "change",
        help="Changes given parameters.",
    )
    parser_2_3.add_argument(
        "--posix_permissions", required=False, default="", type=str, metavar="POSIX_PERMISSIONS_UMASK",
        help="Posix permissions string (eg. 0775)"
    )
    parser_2_3.add_argument(
        "--directory_statistics", required=False, default=None, type=str, metavar="STATUS", choices=["on", "off"],
        help="New status to be set. One of two possible choices - on/off"
    )
    parser_2_3.add_argument(
        "--starting_with", required=False, default=None, type=str, metavar="NAME",
        help="Prefix of instances to remove (default is testModePrefix value from config file)"
    )
    parser_2_3.add_argument(
        "--of_provider", required=False, default="", type=str, metavar="PROVIDER",
        help="Provider of instances to remove"
    )
    parser_2_3.add_argument(
        "--with_more_providers", required=False, action="store_true",
        help="If set, removes instances also when they have more than one supporting provider. "
             "--of-provider must be used"
    )
    parser_2_3.set_defaults(func=run_test_change)

    parser_2_4 = subparser_2.add_parser(
        "connection",
        help="Tests connection to Onezone, Oneproviders and dareg defined in config.",
    )
    parser_2_4.add_argument(
        "--ignore-disabled-status", required=False, action="store_true",
        help="If included, tests will be performed regardless setup"
    )
    parser_2_4.set_defaults(func=runTestConnection)

    parser_3 = subparsers.add_parser(
        "sandbox", help="Run manually a workflow specifed in the file sandbox.py"
    )
    parser_3.add_argument(
        "--var1",
        default="",
        required=False,
        type=str,
        help="Variable which will be set up in sandbox.",
    )
    parser_3.add_argument(
        "--var2",
        default="",
        required=False,
        type=str,
        help="Variable which will be set up in sandbox.",
    )
    parser_3.add_argument(
        "--var3",
        default="",
        required=False,
        type=str,
        help="Variable which will be set up in sandbox.",
    )
    parser_3.set_defaults(func=runSandbox)

    parser_4 = subparsers.add_parser(
        "check-running", help="Only check and change continous import status"
    )
    parser_4.set_defaults(func=runCheck)

    args = parser.parse_args()

    if "func" not in args:
        # call only with test argument, without specifed test action
        if "test" == sys.argv[-1]:
            parser_2.print_help(sys.stdout)
            return

        # call with no task
        parser.print_help(sys.stdout)
        return

    if "remove" == sys.argv[-1]:
        parser_2_2.print_help(sys.stdout)
        return
    if "change" == sys.argv[-1]:
        parser_2_3.print_help(sys.stdout)
        return
    # init singleton class with configuration
    Settings(args.config)
    args.func(args)


if __name__ == "__main__":
    main()
