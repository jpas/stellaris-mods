{
  description = "stellaris mods and modding tools";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, utils, ...  } @ inputs:
    let
      inherit (nixpkgs) lib;
      eachDefaultSystem = f: utils.lib.eachDefaultSystem
        (system: f system (import nixpkgs { inherit system; }));
    in
    (eachDefaultSystem (system: pkgs: {
      devShells.default = pkgs.mkShell {
        shellHook = ''
          export PYTHONPATH=$PWD
          export STELLARIS_DIR="$HOME/.local/share/Steam/steamapps/common/Stellaris"
          export STELLARIS_STATE_DIR="$HOME/.local/share/Paradox Interactive/Stellaris"
        '';

        buildInputs = lib.attrValues {
          inherit (pkgs) python3;
        };
      };
    }));
}
