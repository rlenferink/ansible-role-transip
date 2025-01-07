# Ansible Role: TransIP

Interacts in an idempotent way with the TransIP API for e.g. nameserver
and DNS management.

## Requirements

The python `pyOpenSSL` and `requests` packages are required on the Ansible executor node.

## Role modules

This role contains a couple of Ansible modules used internally in this role:

* [`transip_auth`](./library/transip_auth.py): Responsible for generating an API token with a validity of 1 hour.
The generated API token will be used for interaction with the TransIP API.
* [`transip_dns`](./library/transip_dns.py): Responsible for setting DNS records for the specified domain(s).
* [`transip_nameserver`](./library/transip_nameserver.py): Responsible for setting nameservers for the specified domain(s).

## Role variables

Available variables are listed below, along with default values (see `defaults/main.yml`):

    transip_user: <not set>

The TransIP user to use for interaction with the TransIP API (required).

    transip_private_key: <not set>

The private key for the specified user so an API token can be generated. A key pair needs to be generated in the
[TransIP control panel](https://www.transip.nl/cp/account/api/) and specified here (either in plain text or
as [Ansible Vault](https://docs.ansible.com/ansible/latest/vault_guide/index.html) encrypted value).

    transip_domains: []

The domains to manage and which nameservers and DNS settings to set.

## Example data

```yaml
transip_domains:
  - name: my-domain-1.com
    nameservers: # Use the TransIP nameservers for this domain
      - ns0.transip.net
      - ns1.transip.nl
      - ns2.transip.eu
    dns_records: # All DNS records for the domain, not specified entries will be removed
      - name: www
        expire: 86400
        type: "A"
        content: "1.2.3.4"
        external: false # Optional record, in case this is 'true' the existing record content is taken. This is useful
                        # for e.g. a Dynamic DNS (DDNS) record, which is updated through other means.

  - name: my-domain-2.com
    nameservers: # This domain uses the Cloudflare nameservers; so don't specify DNS records here.
      - kate.ns.cloudflare.com
      - ram.ns.cloudflare.com
```
