#!/usr/bin/env python3
"""Capture an isolated Proton startup using a prepared local game copy."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proton", type=Path, required=True)
    parser.add_argument("--steam", type=Path, required=True)
    parser.add_argument("--seconds", type=int, default=90)
    parser.add_argument("--without-mod", action="store_true")
    parser.add_argument("--mod-first", action="store_true", help="Place Killer App before the base/patch archives to test ordering")
    parser.add_argument("--software-gl", action="store_true", help="Request Mesa software OpenGL and additional GL diagnostics")
    args = parser.parse_args()
    if not 1 <= args.seconds <= 600:
        parser.error("seconds must be between 1 and 600")
    if args.without_mod and args.mod_first:
        parser.error("without-mod and mod-first are mutually exclusive")
    workspace = Path(__file__).resolve().parent.parent
    runtime = workspace / "local/runtime"
    game = runtime / "game"
    if game.is_symlink() or not (game / "Lithtech.exe").is_file():
        parser.error("Prepare a real copy at local/runtime/game first; see docs/RUNTIME_TRACING.md")
    # Refuse symlinked game trees: this runner is intended for copied files only.
    if any(p.is_symlink() for p in game.rglob("*")):
        parser.error("The isolated game copy must not contain symlinks")
    tag = "patch-only" if args.without_mod else ("killer-app-first" if args.mod_first else "killer-app")
    output = runtime / "logs" / f"{tag}-{time.time_ns()}"
    output.mkdir(parents=True)
    compat = runtime / f"compatdata-{tag}"
    compat.mkdir(exist_ok=True)
    env = os.environ.copy()
    env.update({
        "STEAM_COMPAT_DATA_PATH": str(compat),
        "STEAM_COMPAT_CLIENT_INSTALL_PATH": str(args.steam.resolve()),
        "SteamAppId": "327740", "SteamGameId": "327740",
        "PROTON_LOG": "1", "PROTON_LOG_DIR": str(output),
        "WINEDEBUG": "+timestamp,+pid,+loaddll",
        "PROTON_USE_WINED3D": "1", "PROTON_NO_ESYNC": "1", "PROTON_NO_FSYNC": "1",
    })
    if args.software_gl:
        env.update({"LIBGL_ALWAYS_SOFTWARE": "1", "LIBGL_DEBUG": "verbose", "__GLX_VENDOR_LIBRARY_NAME": "mesa"})
    mod_args = ["+mod", "Retail", "-rez", r"Custom\Mods\Retail\Killer_App_Mod.REZ"]
    game_args = mod_args.copy() if args.mod_first else []
    for archive in ["Game.rez", "Sound.rez", "Game2.rez", "Custom", "gamep3.rez",
                    "gamep4.rez", "gamep5.rez", "gamep6.REZ"]:
        game_args += ["-rez", archive]
    if not args.without_mod and not args.mod_first:
        game_args += mod_args
    game_args += ["+multiplayer", "0", "+ScreenWidth", "800", "+ScreenHeight", "600",
                  "+Windowed", "1", "+DisableSound", "1", "+DisableMusic", "1"]
    command = ["xvfb-run", "-a", "-e", str(output / "xvfb.log"), "-s", "-screen 0 1280x720x24", "strace", "-f",
               "-s", "512", "-e", "trace=openat,unlink,rename", "-o", str(output / "files.log"),
               str(args.proton.resolve()), "run", str(game / "Lithtech.exe"), *game_args]
    report = {"command": command, "seconds": args.seconds, "tag": tag,
              "proton": str(args.proton.resolve()), "game": str(game), "snapshots": [],
              "compatdata": str(compat), "environment": {
                  key: env[key] for key in env if key.startswith(("PROTON_", "STEAM_COMPAT_"))
                  or key in {"SteamAppId", "SteamGameId", "WINEDEBUG", "LIBGL_ALWAYS_SOFTWARE", "LIBGL_DEBUG", "__GLX_VENDOR_LIBRARY_NAME"}}}
    seen = set()
    print(f"Startup trace: {output}", flush=True)
    with (output / "console.log").open("wb") as log:
        process = subprocess.Popen(command, cwd=game, env=env, stdout=log,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        deadline = time.monotonic() + args.seconds
        try:
            while process.poll() is None and time.monotonic() < deadline:
                temp_dirs = [compat / "pfx/drive_c/windows/temp",
                             compat / "pfx/drive_c/users/steamuser/Temp",
                             compat / "pfx/drive_c/users/steamuser/AppData/Local/Temp"]
                for folder in temp_dirs:
                    if folder.is_symlink():
                        continue
                    for path in folder.glob("*"):
                        if path.is_symlink() or not path.is_file():
                            continue
                        try:
                            with path.open("rb") as stream:
                                if stream.read(2) != b"MZ":
                                    continue
                                stream.seek(0)
                                data = stream.read()
                        except (OSError, PermissionError):
                            continue
                        digest = hashlib.sha256(data).hexdigest()
                        key = (str(path), digest)
                        if key in seen:
                            continue
                        seen.add(key)
                        destination = output / "modules" / digest
                        destination.parent.mkdir(exist_ok=True)
                        destination.write_bytes(data)
                        report["snapshots"].append({"path": str(path.relative_to(compat)),
                                                    "sha256": digest, "size": len(data),
                                                    "captured_monotonic": time.monotonic()})
                time.sleep(0.25)
            report["timeout"] = process.poll() is None
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
            # Stop only the wineserver associated with this disposable prefix.
            stop_env = env | {"WINEPREFIX": str(compat / "pfx")}
            subprocess.run([str(args.proton.resolve().parent / "files/bin/wineserver"), "-k"],
                           env=stop_env, stdout=log, stderr=log, timeout=10, check=False)
        report["returncode"] = process.returncode
    (output / "trace.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Captured {len(report['snapshots'])} temporary PE snapshots; inspect logs for startup success.")


if __name__ == "__main__":
    main()
