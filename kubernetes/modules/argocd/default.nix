{
  lib,
  config,
  charts,
  ...
}:
let
  cfg = config.services.argocd;

  namespace = "argocd";
  values = lib.attrsets.recursiveUpdate { } cfg.values;
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
