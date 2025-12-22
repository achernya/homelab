{
  lib,
  config,
  charts,
  pkgs,
  ...
}:
let
  cfg = config.services.jellyfin;

  namespace = "jellyfin";
  values = lib.attrsets.recursiveUpdate {
    ingress = {
      enabled = true;
      hosts."" = {
        paths = [
          {
            path = "/";
            pathType = "Prefix";
          }
        ];
      };
    };
    volumes = [
      {
        name = "movies";
        hostPath = {
          path = "/film/Videos/Movies";
          type = "Directory";
        };
      }
      {
        name = "tv";
        hostPath = {
          path = "/film/Videos/TV";
          type = "Directory";
        };
      }
      {
        name = "music";
        hostPath = {
          path = "/film/Videos/Music";
          type = "Directory";
        };
      }
    ];
    volumeMounts = [
      {
        name = "movies";
        mountPath = "/media/Movies";
        readOnly = true;
      }
      {
        name = "tv";
        mountPath = "/media/TV";
        readOnly = true;
      }
      {
        name = "music";
        mountPath = "/media/Music";
        readOnly = true;
      }
    ];
    persistence.config = {
      storageClass = "local-path";
    };
    metrics = {
      enabled = false;
    };
    resources = lib.mkIf config.services.generic-device-plugin.enable {
      limits = {
        "squat.ai/gpu-render" = "1";
      };
    };
  } cfg.values;
in
{
  options.services.jellyfin = with lib; {
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
    applications.jellyfin = {
      inherit namespace;

      createNamespace = true;

      helm.releases.jellyfin = {
        inherit values;
        chart = charts.jellyfin.jellyfin;
      };
    };
  };
}
