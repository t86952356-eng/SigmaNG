#!/usr/bin/env python3
"""
Generates SigmaNG-Android.json - a standalone Minecraft "Client Version" manifest
for Android launchers (Fold Craft Launcher / Zalith / Pojav family).

Design notes (FCL/Pojav backend compatibility):
  * The Pojav/FCL backend (Tools.generateLibClasspath) REQUIRES at least one
    "org.lwjgl:lwjgl:<version>" library entry, otherwise it throws
    "Unable to determine LWJGL version". We keep exactly one vanilla LWJGL 3.2.2
    artifact entry for detection; the launcher injects its own bridged LWJGL
    (3.3.x) FIRST on the classpath and its own natives via
    -Dorg.lwjgl.librarypath, so the game never actually loads LWJGL 3.2.2.
  * Our client jar (downloads.client) is a fat jar containing every other
    dependency, all Minecraft classes, assets and data - identical layout to a
    vanilla client jar.
  * game/jvm arguments and assetIndex are copied verbatim from the official
    vanilla 1.16.4 manifest, plus "-Dsigma.android=true" which disables
    desktop-only features inside the client (Discord RPC, yt-dlp, ...).
  * Bytecode level is Java 17 (source uses Java 16+ syntax), so javaVersion
    requests a JRE 17 runtime.
"""
import argparse
import datetime
import hashlib
import json
import os
import urllib.request

VANILLA_1164_URL = ("https://piston-meta.mojang.com/v1/packages/"
                    "596ad61fda7612d9edf8881cf81869276bdb7f82/1.16.4.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jar", required=True, help="path to SigmaNG-Android.jar")
    ap.add_argument("--client-url", required=True,
                    help="public download URL of the client jar (GitHub release asset)")
    ap.add_argument("--id", default="SigmaNG-Android")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    with urllib.request.urlopen(VANILLA_1164_URL, timeout=60) as resp:
        vanilla = json.load(resp)

    with open(args.jar, "rb") as fh:
        data = fh.read()
    sha1 = hashlib.sha1(data).hexdigest()
    size = len(data)

    # Single LWJGL entry (detection only) - strip natives classifiers.
    lwjgl_entry = None
    for lib in vanilla["libraries"]:
        if lib["name"] == "org.lwjgl:lwjgl:3.2.2":
            lwjgl_entry = {
                "name": lib["name"],
                "downloads": {"artifact": lib["downloads"]["artifact"]},
            }
            break
    if lwjgl_entry is None:
        raise SystemExit("vanilla manifest did not contain org.lwjgl:lwjgl:3.2.2")

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")

    manifest = {
        "id": args.id,
        "type": "release",
        "mainClass": "net.minecraft.client.main.Main",
        "minimumLauncherVersion": vanilla.get("minimumLauncherVersion", 21),
        "javaVersion": {"component": "jre-17", "majorVersion": 17},
        "assetIndex": vanilla["assetIndex"],
        "assets": vanilla["assets"],
        "downloads": {
            "client": {
                "sha1": sha1,
                "size": size,
                "url": args.client_url,
            }
        },
        "libraries": [lwjgl_entry],
        "arguments": {
            "game": vanilla["arguments"]["game"],
            "jvm": list(vanilla["arguments"]["jvm"]) + ["-Dsigma.android=true"],
        },
        "logging": vanilla.get("logging"),
        "releaseTime": now,
        "time": now,
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    print(f"[json] id={args.id}")
    print(f"[json] client sha1={sha1} size={size}")
    print(f"[json] client url={args.client_url}")
    print(f"[json] wrote {args.out}")


if __name__ == "__main__":
    main()
