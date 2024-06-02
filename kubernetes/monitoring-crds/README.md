# monitoring-crds

`monitoring-crds` installs the entire CRDs for the prometheus-based
monitoring stack. It must be installed before the `monitoring` helm
charts.

Follow the instructions on the [kube-prometheus-stack
chart](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack)
to determine which version of the CRDs needs to be installed.
