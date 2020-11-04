#!/usr/bin/env python3

import glob
import os
import urllib.request
import xml.etree.ElementTree as ET

def update_super_manifest_file(super_manifest_file):
    print("Updating {}".format(super_manifest_file))
    super_manifest_tree = ET.parse(super_manifest_file)
    super_manifest_root = super_manifest_tree.getroot()
    for uri_element in super_manifest_root.iter('uri'):
        remote_path = uri_element.text
        local_path = os.path.basename(remote_path)
        yield local_path, remote_path
        uri_element.text = local_path
    for manifest_element in super_manifest_root.iter('board-manifest'):
        remote_path = manifest_element.get('dependency-url')
        if remote_path is not None:
            local_path = os.path.basename(remote_path)
            yield local_path, remote_path
            manifest_element.set('dependency-url', local_path)
    for manifest_element in super_manifest_root.iter('middleware-manifest'):
        remote_path = manifest_element.get('dependency-url')
        if remote_path is not None:
            local_path = os.path.basename(remote_path)
            yield local_path, remote_path
            manifest_element.set('dependency-url', local_path)
    super_manifest_tree.write(super_manifest_file)

def fetch_content_manifests(content_manifest_dict):
    for local_path, remote_path in content_manifest_dict.items():
        print("Pulling {} -> {}".format(remote_path, local_path ))
        urllib.request.urlretrieve(remote_path, local_path)

def main():
    super_manifest_files = list(glob.glob("*super*.xml"))
    content_manifest_dict = dict()
    for super_manifest_file in super_manifest_files:
        for local_path, remote_path in update_super_manifest_file(super_manifest_file):
            if local_path in content_manifest_dict:
                assert(content_manifest_dict[local_path] == remote_path)
            else:
                content_manifest_dict[local_path] = remote_path
    fetch_content_manifests(content_manifest_dict)

if __name__ == '__main__':
    main()
