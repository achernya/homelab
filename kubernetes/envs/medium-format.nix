{
  nixidy.target.repository = "https://github.com/achernya/homelab.git";
  nixidy.target.branch = "nixidy";
  nixidy.target.rootPath = "kubernetes/generated/medium-format";
  nixidy.chartsDir = ../charts;

  imports = [
    ../modules/argocd
    ../modules/generic-device-plugin
    ../modules/jellyfin
  ];

}
