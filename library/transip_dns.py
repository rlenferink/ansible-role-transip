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


def prepare_and_merge_dns_records(existing_records, proposed_records):
    combined_records = []

    for record in proposed_records:
        new_record = {
            # Use the following information to build a TransIP API accepted record
            'name': record['name'],
            'type': record['type'],
            'expire': record['expire'],
            'content': record['content'],
        }

        if 'external' in record and record['external']:
            try:
                existing_record = next(x for x in existing_records
                                       if record['name'] == x['name'] and record['type'] == x['type'])

                # Use value of existing record
                new_record['content'] = existing_record['content']
            except StopIteration:
                raise Exception(f"Unable to find existing 'name={record['name']},type={record['type']}' record")

        combined_records.append(new_record)

    return combined_records


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
    proposed_records = module.params['records']

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
        proposed_records.sort(key=lambda x: (x['name'], x['type'], x['content']), reverse=False)

        # Merge 'external' records from existing records
        combined_records = prepare_and_merge_dns_records(existing_records, proposed_records)

        # Only perform an update if the DNS entries differ
        if existing_records != combined_records:
            update_dns_records(request_headers, domain, combined_records)

            result['domain'] = domain
            result['records'] = combined_records
            result.update(changed=True)
    except Exception as e:
        module.fail_json(msg=f"Error while updating DNS records: {e.args}")

    module.exit_json(**result)


if __name__ == "__main__":
    main()
