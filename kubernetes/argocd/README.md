# argocd-customizations

`argocd-cusetomizations` is the first app installed by ArgoCD when it
starts the synchronization. It configures ArgoCD itself to be able to
successfully sync the later apps.

Currently, this contains two major changes:

1. Ignore CiliumIdentity and related objects, injected by the Cilium
   CNI. Otherwise ArgoCD will see all charts as unsynced and
   repeatedly try to delete them.
1. Change the `instanceLabelKey` away from the default
   `app.kubernetes.io/instance`, as some charts (namely, traefik)
   expect to be able to set this value to their own preferences. This
   prevents labelSelectors from working, as they will now mismatch.
