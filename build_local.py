#!/usr/bin/env python3

from functools import wraps
import argparse
import glob
import os
import time
import urllib.request
import xml.etree.ElementTree as ET

SUPER_MANIFEST_URIS=[
    'https://github.com/cypresssemiconductorco/mtb-super-manifest/raw/v2.X/mtb-super-manifest.xml',
    'https://github.com/cypresssemiconductorco/mtb-super-manifest/raw/v2.X/mtb-super-manifest-fv2.xml'
]

# Copied from https://github.com/saltycrane/retry-decorator/blob/a26fe27/retry_decorator.py
# BSD-3 LICENSE: https://github.com/saltycrane/retry-decorator/blob/a26fe27/LICENSE
# Copyright (c) 2013, SaltyCrane
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the
#    distribution.
#
#  * Neither the name of the SaltyCrane nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
def retry(ExceptionToCheck, tries=4, delay=3, backoff=2, logger=None):
    """Retry calling the decorated function using an exponential backoff.
    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry
    :param ExceptionToCheck: the exception to check. may be a tuple of
        exceptions to check
    :type ExceptionToCheck: Exception or tuple
    :param tries: number of times to try (not retry) before giving up
    :type tries: int
    :param delay: initial delay between retries in seconds
    :type delay: int
    :param backoff: backoff multiplier e.g. value of 2 will double the delay
        each retry
    :type backoff: int
    :param logger: logger to use. If None, print
    :type logger: logging.Logger instance
    """
    def deco_retry(f):

        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck as e:
                    msg = "%s, Retrying in %d seconds..." % (str(e), mdelay)
                    if logger:
                        logger.warning(msg)
                    else:
                        print(msg)
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry

# Workaround for GitHub server randomly closing connections:
# ConnectionResetError: [WinError 10054] An existing connection was forcibly closed by the remote host
@retry(ConnectionResetError, tries=10)
def pull_manifest(remote_path, local_path):
    print("Pulling {} -> {}".format(remote_path, local_path ))
    time.sleep(2)
    urllib.request.urlretrieve(remote_path, local_path)

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
        pull_manifest(remote_path, local_path)

def fetch_super_manifests():
    for remote_path in SUPER_MANIFEST_URIS:
        local_path = os.path.basename(remote_path)
        pull_manifest(remote_path, local_path)
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
