{
  lib,
  config,
  ...
}:
let
  cfg = config.services.generic-device-plugin;
  namespace = "kube-system";
  labels = {
    "app.kubernetes.io/name" = "generic-device-plugin";
  };
in
{
  options.services.generic-device-plugin = with lib; {
    enable = mkOption {
      type = types.bool;
      default = true;
    };
  };
  config = lib.mkIf cfg.enable {
    applications.generic-device-plugin = {
      yamls = [ (builtins.readFile ./daemonset.yaml) ];
    };
  };
}
