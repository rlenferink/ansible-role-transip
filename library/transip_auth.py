#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2023 Roy Lenferink
# Use of this source code is governed by an MIT-style license that can be found in the LICENSE file

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = """
---
module: transip_auth
author: Roy Lenferink (@rlenferink)
short_description: module for generating a TransIP access token
requirements: []
version_added: "0.1.0"
description:
  - Generate an API token to communicate with the TransIP API.
    Consult the README.md for examples for the role.
options: {}
"""


import base64
import datetime
import json
import random
import requests
import string
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes


from ansible.module_utils.basic import AnsibleModule


def get_random_string(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))


def generate_message(user, ro, exp, label, global_key):
    msg = {
        "login": user,
        "nonce": get_random_string(20),
        "read_only": ro,
        "expiration_time": exp,
        "label": label,
        "global_key": global_key
    }
    return json.dumps(msg)


def sign_message(message, private_key):
    pkey = serialization.load_pem_private_key(
        private_key.encode(),
        password=None
    )
    sig = pkey.sign(
            message.encode('utf-8'),
            padding.PKCS1v15(),
            hashes.SHA512()
    )
    sig_base64 = base64.b64encode(sig)
    return sig_base64


def request_api_token(msg, sig):
    response = requests.post('https://api.transip.nl/v6/auth', headers={'Signature': sig}, data=msg)
    if response.ok:
        token = response.json()["token"]
        return token

    raise Exception(response.json()["error"])


def main():
    module = AnsibleModule(
        argument_spec=dict(
            user=dict(required=True),
            read_only=dict(default=False, type='bool'),
            expiration=dict(default='1 hour'),
            label=dict(default='Ansible key'),
            global_key=dict(default=False, type='bool'),
            private_key=dict(required=True, no_log=True),
        ),
        mutually_exclusive=[],
        required_by={},
        supports_check_mode=False
    )

    # Module parameters
    user = module.params['user']
    read_only = module.params['read_only']
    expiration = module.params['expiration']
    label = module.params['label']
    global_key = module.params['global_key']
    private_key = module.params['private_key']

    # Include a timestamp in the label, since token labels need to be unique
    ct = datetime.datetime.now()
    label_ts = f"{label} {ct.year}-{ct.month:02d}-{ct.day:02d} {ct.hour:02d}:{ct.minute:02d}:{ct.second:02d}"

    result = dict(changed=True, warnings=list())

    # Generate message + signature
    msg = generate_message(user, read_only, expiration, label_ts, global_key)
    sig = sign_message(msg, private_key)

    # Generate an API token
    try:
        token = request_api_token(msg, sig)

        result['label'] = label_ts
        result['user'] = user
        result['token'] = token
    except Exception as e:
        module.fail_json(msg=f"Error while requesting access token: {e.args}")

    module.exit_json(**result)


if __name__ == "__main__":
    main()
