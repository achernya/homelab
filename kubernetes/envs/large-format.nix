{
  nixidy.target.repository = "https://github.com/achernya/homelab.git";
  nixidy.target.branch = "nixidy";
  nixidy.target.rootPath = "kubernetes/generated/large-format";
  nixidy.chartsDir = ../charts;

  services.generic-device-plugin.enable = false;

  imports = [
    ../modules/argocd
    ../modules/generic-device-plugin
    ../modules/jellyfin
  ];

}
