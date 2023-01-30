#!/usr/bin/python3

# Generate ansible inventory dynamically, based on the contents of the
# given configuration file (by default, cluster_config.yaml).
#
# To see what this inventory contains, run
#   $ ansible-inventory -i inventory.py --list
# or
#   $ ./inventory.py --list | jq

import argparse
import itertools
import json
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

def vmvars(config):
    vms = []
    
    base_vm_id = 1011
    hypervisors = sorted(all_hypervisors(config))
    
    kubemasters = sorted(all_kubemasters(config))
    for vm, host in zip(kubemasters, itertools.cycle(hypervisors)):
        vms.append({'name': vm, 'host': host, 'vm_id': base_vm_id})
        base_vm_id += 1

    base_vm_id = 1031
    kubelets = sorted(all_kubelets(config))
    for vm, host in zip(kubelets, itertools.cycle(hypervisors)):
        vms.append({'name': vm, 'host': host, 'vm_id': base_vm_id})
        base_vm_id += 1

    return vms

def hostvars(config, hosts=None):
    hypervisors = all_hypervisors(config)
    # If `hosts` is None, then we need to generate all the
    # hostnames. This is the result of concatenating the names of all
    # the VM hosts with the number of kubemasters and kubelets
    if hosts is None:
        hosts = list(hypervisors) + list(all_kubemasters(config)) + list(all_kubelets(config))
              
    result = defaultdict(dict)
    vms = vmvars(config)
    vms_by_host = defaultdict(list)
    for vm in vms:
        vms_by_host[vm['host']].append(vm)

    for host in hosts:
        if host in hypervisors:
            # Hypervisors directly get their hostvars from the underlying template
            result[host].update(config['vm_hosts'][host] or {})
            # And also any vars about the VMs they run
            result[host].update({'all_vms': vms_by_host[host]})
            continue
        # But all other hosts will be managed via ansible-pull, so they get a local connection
        result[host] = {'ansible_connection': 'local'}
        
    return result

def listall(config):
    result = defaultdict(dict)
    result['_meta'] = {'hostvars': hostvars(config)}
    result['kubemasters'] = {'hosts': list(all_kubemasters(config))}
    result['kubelets'] = {'hosts': list(all_kubelets(config))}
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

def main():
    parser = argparse.ArgumentParser(
        'inventory',
        description='Generate ansible inventory for k8s cluster')
    parser.add_argument('--config', default='cluster_config.yaml')
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--list', action='store_true')
    mode.add_argument('--host')

    args = parser.parse_args()
    config = None
    with open(args.config) as f:
        config = yaml.load(f, Loader=Loader)

    result = {}
    if args.host:
        result = hostvars(config, hosts=[args.host])[args.host]
    if args.list:
        result = listall(config)
    print(json.dumps(sort_dict(result)))

if __name__ == '__main__':
    main()
