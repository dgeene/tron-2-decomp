{
  description = "TRON 2.0 native reconstruction and binary analysis tools";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  outputs = { nixpkgs, ... }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
    in {
      devShells = forAllSystems (system:
        let
          pkgs = import nixpkgs { inherit system; };
          common = with pkgs; [
            cmake ninja pkg-config gdb binutils file ripgrep git curl jq
            (python3.withPackages (ps: [ ps.pefile ]))
          ];
          headless = pkgs.writeShellScriptBin "ghidra-headless" ''
            exec ${pkgs.ghidra}/lib/ghidra/support/analyzeHeadless "$@"
          '';
        in {
          default = pkgs.mkShell { packages = common; };
          analysis = pkgs.mkShell {
            packages = common ++ [ pkgs.ghidra pkgs.radare2 headless ];
          };
        });
    };
}
