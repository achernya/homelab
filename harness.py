#!/usr/bin/python3

# Run all of the Ansible playbooks required to form the cluster, in
# the order required.
#
# This helper script replaced manual invocations of the form
#  $ ansible-playbook -i ansible/inventory.py ansible/PLAYBOOK.yml
#
# These invocations work perfectly fine, and are useful for
# development, but require the operator to manually run steps such as
# `kubectl proxy` when necessary.
#
# This script automates not just sequencing, but also managing the
# otherwise-manual steps that don't fit into Ansible's execution
# model.

from collections.abc import Generator
from typing import Any

import argparse
import contextlib
import dataclasses
import os
import pprint
import shutil
import subprocess
import sys

import ansible_runner  # type: ignore


class PlaybookError(Exception):
    pass


@contextlib.contextmanager
def kubectl_args(kubectl_args, *args, **kwargs) -> Generator[None, None, None]:
    p = None
    try:
        p = subprocess.Popen(
            [shutil.which("kubectl")] + kubectl_args, stdout=subprocess.DEVNULL
        )
        yield
    finally:
        if not p:
            return
        p.terminate()
        p.wait()


@contextlib.contextmanager
def kubectl_proxy(*args, **kwargs) -> Generator[None, None, None]:
    with kubectl_args(["proxy"]) as kubectl:
        yield kubectl


@contextlib.contextmanager
def argocd_portfwd(*args, **kwargs) -> Generator[None, None, None]:
    ARGOCD = ["port-forward", "svc/argocd-server", "-n", "argocd", "8080:443"]
    with kubectl_args(ARGOCD) as kubectl:
        yield kubectl


@dataclasses.dataclass
class Step:
    playbook: str
    desc: str
    # Ideally this would be `contextlib.AbstractContextManager`, but
    # that doesn't seem to play well with the decorator
    context: Any = contextlib.nullcontext


STEPS = [
    Step(playbook="create_template.yml", desc="Prepare Debian VM template"),
    Step(playbook="create_vms.yml", desc="Create all Kubernetes VMs"),
    Step(playbook="kubeadm.yml", desc="Form the kubernetes cluster"),
    Step(
        playbook="low_level_apps.yml",
        desc="Install low-level cluster apps",
        context=kubectl_proxy,
    ),
]


def path_to(ansible_resource: str):
    return os.path.join("ansible", ansible_resource)


def get_config(playbook: str):
    return ansible_runner.RunnerConfig(
        private_data_dir=".",
        playbook=path_to(playbook),
        inventory=path_to("inventory.py"),
    )


def run_playbook(desc: str, playbook: str):
    print(desc)
    rc = get_config(playbook)
    rc.prepare()
    r = ansible_runner.Runner(config=rc)
    r.run()
    print("Final status:")
    if r.status != "successful":
        raise PlaybookError(f"Playbook <{playbook}> did not complete successfully")

    pprint.pprint(r.stats)
    print()


def run_steps(steps):
    for i, step in enumerate(steps):
        with step.context():
            run_playbook(f"[{i+1}/{len(steps)}] {step.desc}", step.playbook)


def main():
    parser = argparse.ArgumentParser(
        prog="harness",
        description="Homelab ansible automation harness",
    )
    parser.add_argument(
        "-s",
        "--start_at",
        help="Start the workflow at numbered step",
        type=int,
        choices=range(0, len(STEPS)),
    )
    parser.add_argument(
        "--show_steps",
        action="store_true",
        help="Show steps that would be run",
    )
    args = parser.parse_args()
    desired_steps = STEPS[args.start_at :]
    if args.show_steps:
        for i, step in enumerate(desired_steps):
            print(f"{i}: {step.desc}")
        return
    try:
        run_steps(desired_steps)
    except PlaybookError as e:
        print(e)
        print("You can re-run starting from this step using --start_at=NUM")
        sys.exit(1)


if __name__ == "__main__":
    main()
