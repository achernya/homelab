# Cilium CNI

`cilium` is the container networking infrastructure used in the
cluster. It's already bootstrapped by the Ansible scripts when the
cluster is created, but it's running in a minimal configuration.

This app does not need to be applied early, as it just finishes the
optional customization to add additional capability ot Cilium. For the
most part, this is limited to configuring monitoring (both Prometheus
metrics and the Hubble UI), but also configuring the loadbalancer.
