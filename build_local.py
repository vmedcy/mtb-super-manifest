#!/usr/bin/env python3

import argparse
import glob
import os
import urllib.request
import xml.etree.ElementTree as ET

SUPER_MANIFEST_URIS=[
    'https://github.com/cypresssemiconductorco/mtb-super-manifest/raw/v2.X/mtb-super-manifest.xml',
    'https://github.com/cypresssemiconductorco/mtb-super-manifest/raw/v2.X/mtb-super-manifest-fv2.xml'
]

def update_super_manifest_file(super_manifest_file, uri_prefix):
    print("Updating {}".format(super_manifest_file))
    super_manifest_tree = ET.parse(super_manifest_file)
    super_manifest_root = super_manifest_tree.getroot()
    for uri_element in super_manifest_root.iter('uri'):
        remote_path = uri_element.text
        local_path = os.path.basename(remote_path)
        yield local_path, remote_path
        uri_text = uri_prefix + local_path if uri_prefix else local_path
        uri_element.text = uri_text
    for manifest_element in super_manifest_root.iter('board-manifest'):
        remote_path = manifest_element.get('dependency-url')
        if remote_path is not None:
            local_path = os.path.basename(remote_path)
            yield local_path, remote_path
            uri_text = uri_prefix + local_path if uri_prefix else local_path
            manifest_element.set('dependency-url', uri_text)
    for manifest_element in super_manifest_root.iter('middleware-manifest'):
        remote_path = manifest_element.get('dependency-url')
        if remote_path is not None:
            local_path = os.path.basename(remote_path)
            yield local_path, remote_path
            uri_text = uri_prefix + local_path if uri_prefix else local_path
            manifest_element.set('dependency-url', uri_text)
    super_manifest_tree.write(super_manifest_file)

def fetch_content_manifests(content_manifest_dict):
    for local_path, remote_path in content_manifest_dict.items():
        print("Pulling {} -> {}".format(remote_path, local_path ))
        urllib.request.urlretrieve(remote_path, local_path)

def fetch_super_manifests():
    for remote_path in SUPER_MANIFEST_URIS:
        local_path = os.path.basename(remote_path)
        print("Pulling {} -> {}".format(remote_path, local_path ))
        urllib.request.urlretrieve(remote_path, local_path)
        yield local_path

def main():
    argParser = argparse.ArgumentParser()
    argParser.add_argument("--uri-prefix", help="Base prefix to prepend to all manifest URIs", default=None)
    args = argParser.parse_args()
    super_manifest_files = list(fetch_super_manifests())
    content_manifest_dict = dict()
    for super_manifest_file in super_manifest_files:
        for local_path, remote_path in update_super_manifest_file(super_manifest_file, args.uri_prefix):
            if local_path in content_manifest_dict:
                assert(content_manifest_dict[local_path] == remote_path)
            else:
                content_manifest_dict[local_path] = remote_path
    fetch_content_manifests(content_manifest_dict)

if __name__ == '__main__':
    main()
