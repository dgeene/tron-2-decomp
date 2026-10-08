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
          welcome = name: ''
            export TRON_DEV_SHELL=${name}
            if [[ $- == *i* ]]; then
              PS1="[tron:${name}] $PS1"
              printf '\nTRON ${name} environment ready. Use exit to leave.\n'
              ${if name == "analysis" then "printf 'Run ghidra to open the GUI, or scripts/analyze.sh BINARY for headless analysis.\\n'" else "printf 'Build with: cmake --preset dev && cmake --build --preset dev\\n'"}
            fi
          '';
        in {
          default = pkgs.mkShell {
            packages = common;
            shellHook = welcome "dev";
          };
          analysis = pkgs.mkShell {
            packages = common ++ [ pkgs.ghidra pkgs.radare2 pkgs.strace pkgs.xvfb-run headless ];
            shellHook = welcome "analysis";
          };
        });
    };
}
