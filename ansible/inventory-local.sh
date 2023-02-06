#!/bin/sh
SCRIPT=$(readlink -f "${0}")
ROOTDIR=$(dirname "${SCRIPT}")
exec "${ROOTDIR}/inventory.py" --local "$@"
