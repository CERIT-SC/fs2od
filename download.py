#!/usr/bin/env python3

import argparse
import os
import json

def download_file(onezone, file_id, file_name, directory):
    """
    Download file with given file_id to given directory.
    """
    url = onezone + "/api/v3/onezone/shares/data/" + file_id + "/content"
    command = "curl --output " + directory + os.sep + file_name + " -sL " + url
    os.popen(command)

def process_node(onezone, file_id, directory = "."):
    """
    Process given node (directory or file).
    """
    # get attributes of node (basic information)
    url = onezone + "/api/v3/onezone/shares/data/" + file_id
    command = "curl -sL " + url
    stream = os.popen(command)
    output = stream.read()
    js = json.loads(output)
    node_type = js["type"]
    node_name = js["name"]

    # check if node is directory or folder
    if node_type == "reg":
        download_file(onezone, file_id, node_name, directory)
    elif node_type == "dir":
        # create directory
        os.mkdir(directory + os.sep + node_name)
        
        # get content of new directory
        url = onezone + "/api/v3/onezone/shares/data/" + file_id + "/children"
        command = "curl -sL " + url
        stream = os.popen(command)
        output = stream.read()
        js = json.loads(output)

        # process child nodes
        for child in js['children']:
            process_node(onezone, child['id'], directory + "/" + node_name)
    else:
        print("Error: unknown type of file:", node_type)

def main():
    parser = argparse.ArgumentParser(description='Download whole space or folder from Onedata')
    parser.add_argument("onezone", default="https://datahub.egi.eu", type=str, help="Onezone hostname with protocol")
    parser.add_argument("file_id", type=str, help="File ID of space, directory or file to download")
    args = parser.parse_args()

    process_node(args.onezone, args.file_id)

if __name__ == "__main__":
    main()
