#!/usr/bin/env python3

import argparse
import sys
from pprint import pprint
from settings import Settings
from utils import Logger
import filesystem, test, sandbox

def runScan(args):
    filesystem.scanWatchedDirectories()

def runTest(args):
    if args.remove_instances:
        prefix = args.remove_instances
        test.deleteAllTestInstances(prefix)
    elif args.remove_groups:
        prefix = args.remove_groups
        test.deleteAllTestGroups(prefix)
    elif args.register_space:
        test.registerSpace(args.register_space)
    else:
        Logger.log(1, "No test task set")

def runTestConnection(args):
    test.testConnection()

def runSandbox(args):
    sandbox.sandbox()

def main():
    parser = argparse.ArgumentParser(description='FS2OD - Filesystem to Onedata importing software')
    parser.add_argument("--config", default="config.yaml", required=False, type=str, help="Path to YAML configuration file (default value is ./config.yaml)")
    subparsers = parser.add_subparsers(help='Name of workflow which will be run')
    
    parser_1 = subparsers.add_parser("scan", help="Scan watched directories and import to Onedata")
    parser_1.set_defaults(func=runScan)

    parser_2 = subparsers.add_parser("test", help="Do defined test workflow")
    parser_2.set_defaults(func=runTest)
    parser_2.add_argument("--remove_instances", required=False, type=str, help="Delete all instances (storages, spaces, groups, tokens) with a given prefix.")
    parser_2.add_argument("--remove_groups", required=False, type=str, help="Delete all groups with a given prefix.")
    parser_2.add_argument("--register_space", required=False, type=str, help="Register space - create space (storage, group, token).")

    parser_3 = subparsers.add_parser("test-connection", help="Test if Onezone and Oneprovider is available")
    parser_3.set_defaults(func=runTestConnection)

    parser_4 = subparsers.add_parser("sandbox", help="Do manually edited source file in fs2od evironment - sandbox ")
    parser_4.set_defaults(func=runSandbox)

    args = parser.parse_args()

    if "func" in args:
        # init singleton class with configuration
        Settings(args.config)
        args.func(args)
    else:
        # call with no task
        parser.print_help(sys.stdout)


if __name__ == "__main__":
    main()
