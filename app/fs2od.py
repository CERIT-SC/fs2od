#!/usr/bin/env python3

import argparse
import sys
from pprint import pprint
from settings import Settings
import filesystem, test, sandbox

def runScan(args):
    filesystem.scanWatchedDirectories()

def runTest(args):
    prefix = args.remove_instances
    test.deleteAllTestInstances(prefix)

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
    b_parser.add_argument("--remove_instances", required=True, type=str, help="Delete all instances (storages, spaces, groups, ...) with a given prefix.")
    
    c_parser = subparsers.add_parser("sandbox", help="Do manually edited source file in fs2od evironment - sandbox ")
    c_parser.set_defaults(func=runSandbox)

    args = parser.parse_args()

    # call fs2od with no argument
    if len(sys.argv) <= 1:
        parser.print_help(sys.stdout)
        sys.exit(1)

    if args.func:
        # init singleton class with configuration
        Settings(args.config)
        args.func(args)

if __name__ == "__main__":
    main()
