{
  lib,
  config,
  charts,
  pkgs,
  ...
}:
let
  cfg = config.services.argocd;

  namespace = "argocd";

  origValues = lib.helm.getChartValues charts.argoproj.argo-cd;
  exclusions = origValues.configs.cm."resource.exclusions";
  values = lib.attrsets.recursiveUpdate {
    configs = {
      cm."application.instanceLabelKey" = "argocd.argoproj.io/instance";
      cm."resource.exclusions" = exclusions + ''
        ### Ignore Cilium-generated values
        - apiGroups:
            - cilium.io
          kinds:
            - CiliumIdentity
          clusters:
            - "*"
      '';
    };
  } cfg.values;
in
{
  options.services.argocd = with lib; {
    enable = mkOption {
      type = types.bool;
      default = true;
    };
    values = mkOption {
      type = types.attrsOf types.anything;
      default = { };
    };
  };
  config = lib.mkIf cfg.enable {
    applications.argocd = {
      inherit namespace;

      createNamespace = true;

      helm.releases.argocd = {
        inherit values;
        chart = charts.argoproj.argo-cd;
      };
    };
  };
}
