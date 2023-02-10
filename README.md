# homelab

homelab is a collection of automation for setting up a
highly-available kubernetes cluster, running on VMs on Proxmox.

## Prerequisites

You must have one or more machines installed with proxmox. If using
multiple machines, they should all be joined together to form a
proxmox cluster.

Theoretically, distributed storage is not required, as the kubernetes
system itself will be set up to be highly available. However, this
automation has only been tested on a cluster with ceph-backed VMs.

You need a Debian machine to act as the "controller" from which all
automation is run. Install the dependencies:

```
$ sudo apt install ansible python3-openshift kubernetes-client
```

## Bootstrapping the cluster

The cluster itself is bootstrapped using
[Ansible](https://www.ansible.com/) playbooks. The playbooks are in
the `ansible/` subdirectory. Unlike most Ansible playbooks, which use
an inventory discovery plugin, these playbooks rely on an intent-based
inventory generated by the `inventory.py` script. The inventory
generation takes the parameters in the `cluster_config.yaml` file and
uses them to generate the mapping of VMs to VM hosts. This file needs
to be edited to reflect the available hypervisor infrastructure,
desired number of VMs, and the subnet they will reside in.

Once the cluster config is updated, it's time to run the playbooks. At
this time, there's no meta-automation playbook, so you have to invoke
the playbooks in the right order manually:

1. `create_template.yml`, which fetches a Debian Cloud pre-made image
   and loads it into Proxmox. All subsequent VMs are cloned from this
   base template.
1. `create_vms.yml`, which creates all the VMs. When the number of VMs
   is greater than the number of available VM hosts (hypervisors), the
   VMs will be assigned to the VM hosts round-robin. The VMs will be
   automatically created and they will autoconfigure themselves using
   [cloud-init](https://cloudinit.readthedocs.io/en/latest/), which in
   turn will execute the `cluster_bootstrap.yml` playbook on each VM
   to install its base software. The `cluster_bootstrap.yml` playbook
   is the only playbook that does not need to be executed manually,
   but it does support remote operation if you ever want to make
   updates to the base VMs without fully reinstalling the cluster.
1. `kubeadm.yml`, which bootstraps the kubernetes cluster, joins the
   peer kubemasters for high-availability (if configured), and then
   joins the kubelets. At this point, the cluster is usable, except
   it's still missing a Kubernetes
   [CNI](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/network-plugins/). Copy
   over the `/root/.kube/config` to your "controller" machine so you
   can run `kubectl` locally.
1. `install_apps.yml`, which bootstraps [cilium](https://cilium.io/)
   as the CNI and installs
   [ArgoCD](https://argo-cd.readthedocs.io/en/stable/) to manage the
   rest of the applications. This playbook requires `kubectl proxy` be
   running in the background.

The playbooks can be executed by running

```
$ ansible-playbook -i inventory.py PLAYBOOK_NAME.yml --ask-vault-password
```