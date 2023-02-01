#!/usr/bin/env python3

import argparse
import sys
from pprint import pprint
from settings import Settings
from utils import Logger
import filesystem, test, sandbox


def runScan(args):
    test.testConnection(of_each_host=False)
    filesystem.scanWatchedDirectories()


def runTestRemoveInstances(args):
    test.deleteAllTestInstances(args.prefix)


def runTestRemoveGroups(args):
    test.deleteAllTestGroups(args.prefix)


def runTestRegisterSpace(args):
    test.registerSpace(args.register_space)


def runTestConnection(args):
    test.testConnection(of_each_host=True)


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

    parser_2 = subparsers.add_parser("test", help="Do defined test workflow")
    subparser_2 = parser_2.add_subparsers(help="Name of test workflow which will be run")

    parser_2_1 = subparser_2.add_parser(
        "remove_instances",
        help="Delete all instances (storages, spaces, groups, tokens) with a given prefix (default is testModePrefix value from config file).",
    )
    parser_2_1.add_argument(
        "--prefix", required=False, default="", type=str, help="Prefix of instances to remove"
    )
    parser_2_1.set_defaults(func=runTestRemoveInstances)

    parser_2_2 = subparser_2.add_parser(
        "remove_groups",
        help="Delete all groups with a given prefix (default is testModePrefix value from config file).",
    )
    parser_2_2.add_argument(
        "--prefix", required=False, default="", type=str, help="Prefix of groups to remove"
    )
    parser_2_2.set_defaults(func=runTestRemoveGroups)

    parser_2_3 = subparser_2.add_parser(
        "register_space", help="Register space - create space (storage, group, token)."
    )
    parser_2_3.add_argument("--path", required=True, type=str, help="Path to space")
    parser_2_3.set_defaults(func=runTestRegisterSpace)

    parser_3 = subparsers.add_parser(
        "test-connection", help="Test if Onezone and Oneprovider is available"
    )
    parser_3.set_defaults(func=runTestConnection)

    parser_4 = subparsers.add_parser(
        "sandbox", help="Run manually a workflow specifed in the file sandbox.py"
    )
    parser_4.add_argument(
        "--var1",
        default="",
        required=False,
        type=str,
        help="Variable which will be set up in sandbox.",
    )
    parser_4.add_argument(
        "--var2",
        default="",
        required=False,
        type=str,
        help="Variable which will be set up in sandbox.",
    )
    parser_4.add_argument(
        "--var3",
        default="",
        required=False,
        type=str,
        help="Variable which will be set up in sandbox.",
    )
    parser_4.set_defaults(func=runSandbox)

    parser_5 = subparsers.add_parser(
        "check-running", help="Only check and change continous import status"
    )
    parser_5.set_defaults(func=runCheck)

    args = parser.parse_args()

    if "func" in args:
        # init singleton class with configuration
        Settings(args.config)
        args.func(args)
    else:
        # call only with test argument, without specifed test action
        if "test" == sys.argv[-1]:
            parser_2.print_help(sys.stdout)
            return

        # call with no task
        parser.print_help(sys.stdout)


if __name__ == "__main__":
    main()
