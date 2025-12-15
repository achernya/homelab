{
  nixidy.target.repository = "https://github.com/achernya/homelab.git";
  nixidy.target.branch = "nixidy";
  nixidy.target.rootPath = "kubernetes/generated/parallax";
  nixidy.chartsDir = ../charts;

  imports = [
    ../modules/argocd
  ];
}
