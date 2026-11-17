#!/usr/bin/env python3
"""
SigmaNG Android exclusion auditor (added in v14.3).

Validates the jars excluded from the Android fat jar (SKIP_LIB_EXACT in
package_client.py) against LIB-TO-LIB references — the class of dependency a
source-level grep cannot see. In v14.2 snakeyaml was excluded because nothing
in src/ imports it, but ViaVersion's own jars reference it internally, which
crashed the game on device:
  NoClassDefFoundError: org/yaml/snakeyaml/constructor/BaseConstructor
    at ...vialoadingbase.platform.ViaVersionPlatformImpl.<init>

How it works: parse the constant pool of every class in the *merged* set
(compiled project classes + every lib jar that survives SKIP rules) using the
same parser as trim_libraries.py, and report any reference pointing INTO a
package owned by an excluded jar. A hit is not automatically fatal — each hit
must be judged (guarded call site, never-loaded platform path, ...) — but a
hit with no guard means the jar must be merged back.

MUST-STAY-MERGED (lib-to-lib, learned the hard way):
  snakeyaml-2.0.jar  <- referenced by com.viaversion.viaversion.util.Config
                        and compatibility/Yaml*Compat (6 classes).

Usage:
  javac ... -d build/classes @build/sources.txt        # same as CI
  python3 android/audit_exclusions.py --classes build/classes
Exit code 0 = no references into excluded jars found.
"""
import argparse
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trim_libraries import parse_class_refs  # reuse exact parser

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIBS = os.path.join(REPO, "libs")

# jars excluded by package_client.py SKIP_LIB_EXACT (minus jinput, which is
# skipped by prefix rules and has no classes anyway) -> owning packages.
# Kept in sync with package_client.py manually; verified for v14.3.
EXCLUDED = {
    "jave-1.0.2.jar": ["ws/schild/jave"],
    "jna-4.4.0.jar": ["com/sun/jna"],
    "platform-3.4.0.jar": ["com/sun/jna/platform"],
    "junixsocket-common-2.6.2.jar": ["org/newsclub/net/unix"],
    "junixsocket-native-common-2.6.2.jar": ["org/newsclub/net/unix/native"],
    "joda-time-2.12.5.jar": ["org/joda/time"],
    "google-api-services-analytics-v3-rev169-1.25.0.jar": ["com/google/api/services/analytics"],
    "google-api-services-youtubereporting-v1-rev748-1.25.0.jar": ["com/google/api/services/youtubereporting"],
    "google-api-services-youtubeAnalytics-v2-rev272-1.25.0.jar": ["com/google/api/services/youtubeAnalytics"],
}

# jars never merged for other reasons (keep in sync with package_client.py)
SKIP_LIB_PREFIXES = ("lwjgl", "lombok-")
SKIP_LIB_SUFFIXES = ("-sources.jar", "-javadoc.jar")
SKIP_LIB_EXTRA = {
    "jinput-2.0.5.jar",
    "text2speech-1.11.3-natives-windows.jar",
    # must stay merged (see docstring):
    "snakeyaml-2.0.jar",
}


# Call sites that reference excluded jars but were hand-verified as safe
# (guarded by try-catch-Throwable, behind a guarded Class.forName, or on a
# code path that never loads on Android). Evidence: ANDROID-PORT.md, v14.3
# section. A hit NOT in this set fails the audit.
KNOWN_SAFE = {
    # jna: NarratorLinux.<clinit> wraps NativeLibrary.getInstance/Native.register
    # in try-catch-Throwable -> silent no-op narrator (libraryFound=false);
    # NarratorWindows is never selected because os.name=Linux on Android.
    "com/mojang/text2speech/NarratorLinux",
    "com/mojang/text2speech/NarratorWindows",
    "com/mojang/text2speech/NarratorWindows$Message",
    # jna/platform via oshi: Windows-only code paths, never linked on Linux;
    # the only Android-reachable oshi caller (GLX._init) wraps it in
    # try-catch-Throwable (device log proves it: "CPU: <unknown>").
    "oshi/SystemInfo",
    "oshi/software/os/windows/nt/OSNativeSystemInfo",
    "oshi/software/os/windows/nt/OSVersionInfoEx",
    "oshi/software/os/windows/WindowsHardwareAbstractionLayer",
    "oshi/software/os/windows/nt/GlobalMemory",
    # joda-time: fastjson registers JodaCodec only behind
    # Class.forName("org.joda.time...") inside try-catch-Throwable
    # (ParserConfig.getDeserializer bytecode range 612-742).
    "com/alibaba/fastjson/serializer/JodaCodec",
    # junixsocket: only com.jagrosh DiscordIPC, whose entry point is disabled
    # on Android builds via -Dsigma.android=true (DiscordRPC.java guard).
    "com/jagrosh/discordipc/entities/pipe/UnixPipe",
}


def roots_of_jar(path):
    """All package roots actually present inside a jar."""
    roots = set()
    with zipfile.ZipFile(path) as zf:
        for n in zf.namelist():
            if n.endswith(".class"):
                parts = n[:-6].split("/")
                if len(parts) > 1:
                    roots.add("/".join(parts[:-1]))
    return roots


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--classes", required=True,
                    help="compiled project classes directory (build/classes)")
    args = ap.parse_args()

    # class-name prefix -> owning excluded jar (longest prefixes first)
    excl_prefixes = []
    for jar, pkgs in EXCLUDED.items():
        p = os.path.join(LIBS, jar)
        if not os.path.isfile(p):
            print(f"!! {jar} not found in libs/")
            continue
        for r in roots_of_jar(p):
            excl_prefixes.append((r, jar))
        for pkg in pkgs:
            excl_prefixes.append((pkg, jar))
    excl_prefixes = sorted(set(excl_prefixes), key=lambda t: -len(t[0]))

    def owner_of(ref):
        for pref, jar in excl_prefixes:
            if ref == pref or ref.startswith(pref + "/"):
                return jar
        return None

    hits = {}

    def scan(name_data_iter):
        for name, data in name_data_iter:
            if not name.endswith(".class"):
                continue
            refs = parse_class_refs(data)
            if refs is None:
                continue
            cls = name[:-6]
            for r in refs:
                owner = owner_of(r)
                if owner:
                    hits.setdefault(owner, []).append((cls, r))

    # 1) project classes
    proj = args.classes
    files = []
    for root, _d, fs in os.walk(proj):
        for f in fs:
            if f.endswith(".class"):
                full = os.path.join(root, f)
                rel = os.path.relpath(full, proj).replace(os.sep, "/")
                files.append((rel, open(full, "rb").read()))
    print(f"[audit] project classes: {len(files)}")
    scan(files)

    # 2) merged libs (everything that survives the packer's skip rules)
    merged = 0
    for f in sorted(os.listdir(LIBS)):
        if not f.endswith(".jar"):
            continue
        if f.startswith(SKIP_LIB_PREFIXES) or f.endswith(SKIP_LIB_SUFFIXES):
            continue
        if f in SKIP_LIB_EXTRA or f in EXCLUDED:
            continue
        merged += 1
        with zipfile.ZipFile(os.path.join(LIBS, f)) as zf:
            stream = [(i.filename, zf.read(i)) for i in zf.infolist()
                      if i.filename.endswith(".class")]
        scan(stream)
    print(f"[audit] merged libs scanned: {merged}")

    if not hits:
        print("\n[audit] RESULT: no merged/project class references any excluded jar. All exclusions safe.")
        return 0

    unknown = {jar: [x for x in lst if x[0] not in KNOWN_SAFE]
               for jar, lst in hits.items()}
    unknown = {jar: lst for jar, lst in unknown.items() if lst}

    print("\n[audit] RESULT: references INTO excluded jars found:")
    for jar, lst in sorted(hits.items()):
        classes = sorted({c for c, _ in lst})
        refs = sorted({r for _, r in lst})
        tag = " (all pre-verified safe)" if not unknown.get(jar) else " (HAS UNVERIFIED HITS)"
        print(f"\n== {jar}  ({len(classes)} referencing classes, {len(refs)} distinct refs){tag}")
        for c in classes[:12]:
            mark = "" if c in KNOWN_SAFE else "   <-- UNVERIFIED"
            print(f"   {c}{mark}")
        if len(classes) > 12:
            print(f"   ... +{len(classes)-12} more")

    if unknown:
        print("\n[audit] FAIL: unverified references into excluded jars:")
        for jar, lst in unknown.items():
            for cls, ref in sorted(set(lst)):
                print(f"   {jar} <- {cls} ({ref})")
        print("Either merge the jar back into the fat jar or verify+document the call site.")
        return 1
    print("\n[audit] PASS: every hit is a pre-verified-safe call site (see KNOWN_SAFE).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
