{
  description = "achernya homelab";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-25.05";
    systems.url = "github:nix-systems/default";
    flake-utils.url = "github:numtide/flake-utils";
    treefmt-nix = {
      url = "github:numtide/treefmt-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    nixidy = {
      url = "github:arnarg/nixidy";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };
  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      treefmt-nix,
      nixidy,
      systems,
    }:
    # From nixfmt-tree instructions. Not really compatible with eachDefaultSystem.
    let
      eachSystem = f: nixpkgs.lib.genAttrs (import systems) (system: f nixpkgs.legacyPackages.${system});
      treefmtEval = eachSystem (pkgs: treefmt-nix.lib.evalModule pkgs ./treefmt.nix);
    in
    {
      formatter = eachSystem (pkgs: treefmtEval.${pkgs.system}.config.build.wrapper);
    }
    # Most things go here.
    // (flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs {
          inherit system;
        };
      in
      {
        nixidyEnvs = nixidy.lib.mkEnvs {
          inherit pkgs;

          charts = { };

          envs = {
            parallax.modules = [ ./kubernetes/envs/parallax.nix ];
          };

        };

        # Make `nix run .#nixidy` available.
        packages.nixidy = nixidy.packages.${system}.default;

        # Enable `nix develop`.
        devShells.default = pkgs.mkShell {
          buildInputs = [ nixidy.packages.${system}.default ];
        };
      }
    ));
}
