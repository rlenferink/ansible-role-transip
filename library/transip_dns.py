#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2023 Roy Lenferink
# Use of this source code is governed by an MIT-style license that can be found in the LICENSE file

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = """
---
module: transip_dns
author: Roy Lenferink (@rlenferink)
short_description: module for managing DNS records for a TransIP domain
version_added: "0.1.0"
description:
  - Ensure the DNS records are set for the given domain.
    Consult the README.md for examples for the role.
options: {}
"""


import json
import requests

from ansible.module_utils.basic import AnsibleModule


def fetch_dns_records(headers, domain_name):
    response = requests.get(f'https://api.transip.nl/v6/domains/{domain_name}/dns', headers=headers)
    if response.ok:
        records = response.json()["dnsEntries"]
        return records

    raise Exception(response.json()["error"])


def update_dns_records(headers, domain_name, records):
    data = {
        "dnsEntries": records
    }

    response = requests.put(f'https://api.transip.nl/v6/domains/{domain_name}/dns', headers=headers,
                            data=json.dumps(data))
    if response.ok:
        return

    raise Exception(response.json()["error"])


def main():
    module = AnsibleModule(
        argument_spec=dict(
            token=dict(required=True, no_log=True),
            domain=dict(required=True),
            records=dict(required=True, type='list'),
        ),
        mutually_exclusive=[],
        required_by={},
        supports_check_mode=False
    )

    # Module parameters
    token = module.params['token']
    domain = module.params['domain']
    records = module.params['records']

    # Headers to use for communication with the TransIP API
    request_headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }

    result = dict(changed=False, warnings=list())

    try:
        # Get the existing DNS records
        existing_records = fetch_dns_records(request_headers, domain)

        # Sort the records before comparing, order doesn't matter for DNS records
        existing_records.sort(key=lambda x: (x['name'], x['type'], x['content']), reverse=False)
        records.sort(key=lambda x: (x['name'], x['type'], x['content']), reverse=False)

        # Only perform an update if the DNS entries differ
        if existing_records != records:
            update_dns_records(request_headers, domain, records)

            result['domain'] = domain
            result['records'] = records
            result.update(changed=True)
    except Exception as e:
        module.fail_json(msg=f"Error while updating DNS records: {e.args}")

    module.exit_json(**result)


if __name__ == "__main__":
    main()
