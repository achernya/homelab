#!/bin/bash
set -euf -o pipefail

: "${HELM:=helm}"
: "${AWK:=awk}"

AWKSCRIPT='
# Skip empty lines
/^\s*$/ { next; }
# Skip the header, which starts with NAME
$1 == "NAME" { next; }
# Skip no-dependencies warning
/^WARNING: no dependencies at / { next; }
# Process lines that actually contain information
$4 != "ok" { print $1; }
'

"${HELM}" dependency list "${1}" | "${AWK}" "${AWKSCRIPT}"
