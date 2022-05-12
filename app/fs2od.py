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

def runSandbox(args):
    sandbox.sandbox()

def main():
    parser = argparse.ArgumentParser(description='FS2OD - Filesystem to Onedata importing software')
    parser.add_argument("--config", default="config.yaml", required=False, type=str, help="Path to YAML configuration file (default value is ./config.yaml)")
    subparsers = parser.add_subparsers(help='Name of workflow which will be run')
    
    a_parser = subparsers.add_parser("scan", help="Scan watched directories and import to Onedata")
    a_parser.set_defaults(func=runScan)

    b_parser = subparsers.add_parser("test", help="Do some test workflow")
    b_parser.set_defaults(func=runTest)
    b_parser.add_argument("--remove_instances", required=False, type=str, help="Delete all instances (storages, spaces, groups, tokens) with a given prefix.")
    b_parser.add_argument("--remove_groups", required=False, type=str, help="Delete all groups with a given prefix.")
    b_parser.add_argument("--register_space", required=False, type=str, help="Register space - create space (storage, group, token).")
    
    c_parser = subparsers.add_parser("sandbox", help="Do manually edited source file in fs2od evironment - sandbox ")
    c_parser.set_defaults(func=runSandbox)

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
