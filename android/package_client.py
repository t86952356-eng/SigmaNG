#!/usr/bin/env python3
"""
SigmaNG Android packer.

Builds the standalone client JAR ("Client Version") for Android launchers
(Fold Craft Launcher / Pojav-style launchers) with GL4ES-compatible renderers.

Output layout mirrors a vanilla Minecraft client jar:
  - all compiled project classes (full Minecraft 1.16.4 source + SigmaNG client code)
  - assets/ and data/ resource trees from src/
  - every bundled library EXCEPT LWJGL (the Android launcher injects its own
    bridged LWJGL 3.3.x build, which must never be shadowed) and compile-only
    jars (lombok / sources / javadoc)

Usage:
  python3 package_client.py --src <repo>/src --libs <repo>/libs --classes <build_classes> --out dist/SigmaNG-Android.jar
"""
import argparse
import hashlib
import os
import sys
import zipfile

SKIP_LIB_PREFIXES = ("lwjgl", "lombok-")
SKIP_LIB_SUFFIXES = ("-sources.jar", "-javadoc.jar")
SKIP_LIB_EXACT = {"jinput-2.0.5.jar"}

# Entries never copied out of merged libraries
SKIP_META = ("META-INF/MANIFEST.MF", "META-INF/module-info.class")
SKIP_META_DIR = ("META-INF/versions/",)
SKIP_META_EXT = (".SF", ".RSA", ".DSA", ".EC")
SERVICES_DIR = "META-INF/services/"


def merge_lib(jar_path: str, entries: dict, services: dict):
    with zipfile.ZipFile(jar_path, "r") as zf:
        for info in zf.infolist():
            name = info.filename
            if name.endswith("/"):
                continue
            if name in SKIP_META or name.endswith(SKIP_META_EXT):
                continue
            if any(name.startswith(p) for p in SKIP_META_DIR):
                continue
            if name.startswith(SERVICES_DIR):
                key = name
                data = zf.read(info)
                if key not in services:
                    services[key] = data
                else:
                    services[key] = services[key].rstrip(b"\n") + b"\n" + data.lstrip()
                continue
            if name in entries:
                continue  # first occurrence wins (project classes take priority)
            entries[name] = zf.read(info)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="repo src/ directory")
    ap.add_argument("--libs", required=True, help="repo libs/ directory")
    ap.add_argument("--classes", required=True, help="compiled classes directory")
    ap.add_argument("--out", required=True, help="output jar path")
    args = ap.parse_args()

    entries = {}      # path -> bytes
    services = {}     # META-INF/services/* -> concatenated bytes

    # 1) project classes first -> always win over library copies
    for root, _dirs, files in os.walk(args.classes):
        for f in files:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, args.classes).replace(os.sep, "/")
            with open(full, "rb") as fh:
                entries[rel] = fh.read()

    # 2) resources from src (assets/, data/, root descriptors) - do not overwrite classes
    resource_roots = ["assets", "data"]
    resource_files = ["pack.mcmeta", "pack.png", "log4j2.xml", "version.json"]
    for rootname in resource_roots:
        base = os.path.join(args.src, rootname)
        if not os.path.isdir(base):
            continue
        for root, _dirs, files in os.walk(base):
            for f in files:
                full = os.path.join(root, f)
                rel = os.path.relpath(full, args.src).replace(os.sep, "/")
                if rel in entries:
                    continue
                with open(full, "rb") as fh:
                    entries[rel] = fh.read()
    for rf in resource_files:
        full = os.path.join(args.src, rf)
        if os.path.isfile(full):
            rel = rf
            if rel not in entries:
                with open(full, "rb") as fh:
                    entries[rel] = fh.read()

    # 3) merged libraries
    merged = []
    skipped = []
    for f in sorted(os.listdir(args.libs)):
        if not f.endswith(".jar"):
            continue
        if f.startswith(SKIP_LIB_PREFIXES):
            skipped.append(f)
            continue
        if f.endswith(SKIP_LIB_SUFFIXES) or f in SKIP_LIB_EXACT:
            skipped.append(f)
            continue
        merge_lib(os.path.join(args.libs, f), entries, services)
        merged.append(f)

    out_dir = os.path.dirname(os.path.abspath(args.out))
    os.makedirs(out_dir, exist_ok=True)

    manifest = (
        "Manifest-Version: 1.0\r\n"
        "Main-Class: net.minecraft.client.main.Main\r\n"
        "Implementation-Title: SigmaNG-Android\r\n"
        "Implementation-Version: 14.1-android\r\n"
        "Specification-Title: SigmaNG Client Version (FCL + GL4ES)\r\n"
    ).encode("utf-8")

    with zipfile.ZipFile(args.out, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.writestr("META-INF/MANIFEST.MF", manifest)
        for name, data in services.items():
            zf.writestr(name, data)
        for name, data in entries.items():
            zf.writestr(name, data)

    size = os.path.getsize(args.out)
    with open(args.out, "rb") as fh:
        sha1 = hashlib.sha1(fh.read()).hexdigest()

    print(f"[pack] merged {len(merged)} libraries")
    print(f"[pack] skipped {len(skipped)} jars (lwjgl/lombok/sources/javadoc)")
    print(f"[pack] entries: {len(entries) + len(services) + 1}")
    print(f"[pack] output: {args.out}")
    print(f"[pack] size: {size}")
    print(f"[pack] sha1: {sha1}")


if __name__ == "__main__":
    sys.exit(main())
