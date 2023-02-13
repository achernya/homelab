# acme-dns

`acme-dns` is a custom Helm chart for the
[acme-dns](https://github.com/joohoi/acme-dns) self-hosted DNS that
provides a programmatic API for responding to ACME DNS01 challenges,
which in turn allow for issuing DNS wildcard certificates.

The eventual goal is for this chart to be usable with the
[cert-manager](https://cert-manager.io/docs/installation/helm/) chart.
cert-manager doesn't require acme-dns, but the other alternatives
require Cloud hosted services, some of which are paid.

There is a related project called
[kubernetes-acme-dns-registrar](https://github.com/bitsofinfo/kubernetes-acme-dns-registrar)
(which also assumes there's a functional acme-dns instance), and adds
automatic creation of acme-dns registration secrets for each Ingress
object. However, since that's quite frankly overkill for a single
wildcard certificate (which is the envisioned deployment for most
users), this chart hopes to manage the acme-dns secret minimally and
automatically.

This chart makes use of a small Go program called
[k8s-secret-writer](https://github.com/achernya/k8s-secret-writer) to
write the secret.
