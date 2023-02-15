#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2023 Roy Lenferink
# Use of this source code is governed by an MIT-style license that can be found in the LICENSE file

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = """
---
module: transip_nameserver
author: Roy Lenferink (@rlenferink)
short_description: module for managing nameservers for a TransIP domain
version_added: "0.1.0"
description:
  - Ensure the nameservers are set for the given domain.
    Consult the README.md for examples for the role.
options: {}
"""


import json
import requests

from ansible.module_utils.basic import AnsibleModule


def fetch_nameservers(headers, domain_name):
    response = requests.get(f'https://api.transip.nl/v6/domains/{domain_name}/nameservers', headers=headers)
    if response.ok:
        nameservers = response.json()["nameservers"]
        return nameservers

    raise Exception(response.json()["error"])


def update_nameservers(headers, domain_name, nameservers):
    data = {
        "nameservers": nameservers
    }

    response = requests.put(f'https://api.transip.nl/v6/domains/{domain_name}/nameservers', headers=headers,
                            data=json.dumps(data))
    if response.ok:
        return

    raise Exception(response.json()["error"])


def main():
    module = AnsibleModule(
        argument_spec=dict(
            token=dict(required=True, no_log=True),
            domain=dict(required=True),
            nameservers=dict(required=True, type='list'),
        ),
        mutually_exclusive=[],
        required_by={},
        supports_check_mode=False
    )

    # Module parameters
    token = module.params['token']
    domain = module.params['domain']
    nameservers = module.params['nameservers']

    # Headers to use for communication with the TransIP API
    request_headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }

    result = dict(changed=False, warnings=list())

    try:
        # Get the existing nameservers
        existing_nameservers = fetch_nameservers(request_headers, domain)

        # Only update the nameservers if they differ
        # Do not sort them before comparing, since the order of items is important
        # (e.g. primary vs secondary nameserver)
        if existing_nameservers != nameservers:
            update_nameservers(request_headers, domain, nameservers)

            result['domain'] = domain
            result['nameservers'] = nameservers
            result.update(changed=True)
    except Exception as e:
        module.fail_json(msg=f"Error while updating nameservers: {e.args}")

    module.exit_json(**result)


if __name__ == "__main__":
    main()
