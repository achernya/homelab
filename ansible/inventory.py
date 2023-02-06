#!/usr/bin/python3

# Generate ansible inventory dynamically, based on the contents of the
# given configuration file (by default, cluster_config.yaml).
#
# To see what this inventory contains, run
#   $ ansible-inventory -i inventory.py --list
# or
#   $ ./inventory.py --list | jq

import argparse
import ipaddress
import itertools
import json
import os
import yaml

from collections import defaultdict, OrderedDict

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

def all_hypervisors(config):
    return set(config['vm_hosts'].keys())

def all_kubemasters(config):
    return set(['kubemaster-{:02d}'.format(x+1) for x in range(config['kubemasters'])])

def all_kubelets(config):
    return set(['kubelet-{:02d}'.format(x+1) for x in range(config['kubelets'])])

def all_haproxies(config):
    if config['api_mode'] != 'dedicated-vm':
        return set()
    return set(['haproxy-{:02d}'.format(x+1) for x in range(config['haproxies'])])

def k8s_api_vip(config):
    subnet = ipaddress.ip_network(config['vm_subnet'])
    if config['api_mode'] == 'direct':
        # Return the IP of the first kubemaster
        return subnet.network_address + 11
    # stacked or dedicated-vm, use a VIP
    return subnet.network_address + 20

def k8s_api_port(config):
    if config['api_mode'] == 'direct':
        return 6443
    return 8443

def k8s_api_vars(config):
    return {
        'k8s_api_mode': config['api_mode'],
        'k8s_api_port': k8s_api_port(config),
        'k8s_api_vip': str(k8s_api_vip(config)),
    }

def vmvars(config):
    vms = []

    subnet = ipaddress.ip_network(config['vm_subnet'])

    base_vm_id = 1011
    base_network_addr = subnet.network_address + 11
    hypervisors = sorted(all_hypervisors(config))

    kubemasters = sorted(all_kubemasters(config))
    for vm, host in zip(kubemasters, itertools.cycle(hypervisors)):
        vms.append({'name': vm, 'host': host, 'vm_id': base_vm_id, 'ip': str(base_network_addr)})
        base_vm_id += 1
        base_network_addr += 1

    base_vm_id = 1021
    base_network_addr = subnet.network_address + 21
    haproxies = sorted(all_haproxies(config))
    for vm, host in zip(haproxies, itertools.cycle(hypervisors)):
        vms.append({'name': vm, 'host': host, 'vm_id': base_vm_id, 'ip': str(base_network_addr)})
        base_vm_id += 1
        base_network_addr += 1

    base_vm_id = 1031
    base_network_addr = subnet.network_address + 31
    kubelets = sorted(all_kubelets(config))
    for vm, host in zip(kubelets, itertools.cycle(hypervisors)):
        vms.append({'name': vm, 'host': host, 'vm_id': base_vm_id, 'ip': str(base_network_addr)})
        base_vm_id += 1
        base_network_addr += 1

    return vms

def hostvars(args, config, hosts=None):
    hypervisors = all_hypervisors(config)
    # If `hosts` is None, then we need to generate all the
    # hostnames. This is the result of concatenating the names of all
    # the VM hosts with the number of kubemasters and kubelets
    if hosts is None:
        hosts = list(hypervisors) + list(all_kubemasters(config)) + list(all_kubelets(config)) + list(all_haproxies(config))

    result = defaultdict(dict)
    vms = vmvars(config)
    vms_by_host = defaultdict(list)
    for vm in vms:
        vms_by_host[vm['host']].append(vm)
    vms_by_name = {}
    for vm in vms:
        vms_by_name[vm['name']] = vm

    api_vars = k8s_api_vars(config)

    for host in hosts:
        if host in hypervisors:
            # Hypervisors directly get their hostvars from the underlying template
            result[host].update(config['vm_hosts'][host] or {})
            # And also any vars about the VMs they run
            result[host].update({'all_vms': vms_by_host[host]})
            continue
        result[host] = {'ansible_connection': 'ssh',
                        'ansible_user': 'root',
                        'ansible_host': vms_by_name[host]['ip'],
                        'ansible_ssh_common_args': '-o StrictHostKeyChecking=no'}
        # If we're running under ansible-pull, override
        # ansible_connection to be local, despite still specifying
        # ansible_host.
        if args.local:
            result[host].update({'ansible_connection': 'local'})
        # Add in kubernetes API vars for VMs
        result[host].update(api_vars)

    return result

def listall(args, config):
    result = defaultdict(dict)
    result['_meta'] = {'hostvars': hostvars(args, config)}
    result['kubemasters'] = {'hosts': list(all_kubemasters(config))}
    result['kubelets'] = {'hosts': list(all_kubelets(config))}
    result['haproxies'] = {'hosts': list(all_haproxies(config))}
    result['hypervisors'] = {'hosts': list(all_hypervisors(config))}
    result['ungrouped'] = {'hosts': []}

    all_groups = set(result.keys())
    all_groups.remove('_meta')
    result['all'] = {'children': list(all_groups)}

    return result

def sort_dict(d):
    d = OrderedDict(sorted(d.items()))
    for key, value in d.items():
        if isinstance(value, dict):
            d[key] = sort_dict(value)
            continue
        if isinstance(value, list):
            try:
                d[key] = sorted(value)
            except:
                pass
            continue
    return d

def config_path(filename):
    # First, look for the file in the current working directory. If it
    # exists, use that.
    if os.path.exists(filename):
        return filename
    # Next, check to see if it's next to this script
    selfdir = os.path.dirname(__file__)
    candidate = os.path.join(selfdir, filename)
    if os.path.exists(candidate):
        return candidate
    # Fallback: return the default path for a less-confusing error message
    return filename

def main():
    parser = argparse.ArgumentParser(
        'inventory',
        description='Generate ansible inventory for k8s cluster')
    parser.add_argument('--config', default='cluster_config.yaml')
    parser.add_argument('--local', action='store_true',
                        help='If set, generate ansible_connection: local for VMs')
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--list', action='store_true')
    mode.add_argument('--host')

    args = parser.parse_args()
    config = None
    with open(config_path(args.config)) as f:
        config = yaml.load(f, Loader=Loader)

    result = {}
    if args.host:
        result = hostvars(args, config, hosts=[args.host])[args.host]
    if args.list:
        result = listall(args, config)
    print(json.dumps(sort_dict(result)))

if __name__ == '__main__':
    main()
