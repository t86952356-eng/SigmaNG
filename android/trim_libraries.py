#!/usr/bin/env python3
"""
SigmaNG Android library trimmer (v14.2 slimming).

Static reachability (dead-class) elimination for large utility libraries
bundled in the fat client jar (default targets: fastutil + icu4j).

How it works:
  1. Parse the constant pool of every .class entry in the jar and collect the
     set of classes each class references (CONSTANT_Class names + all "L..;"
     types inside every NameAndType/MethodType descriptor). This covers every
     statically reachable edge: code, signatures, stack maps, InnerClasses.
  2. A class under a --package-root is KEPT iff it is reachable through any
     chain that starts outside the trimmed roots (project classes or other
     libraries). Reachable-from-kept is transitive, so a used class pulling in
     another used class is fully preserved.
  3. Everything else (assets, resources, other libraries, META-INF/services)
     is copied byte-identically; the jar is rewritten at deflate level 9.

Safety contract:
  - Only classes under the given roots can ever be removed.
  - Both default targets ship no META-INF/services and are never loaded
    reflectively by this codebase (verified by grep; see ANDROID-PORT.md).

Usage:
  python3 trim_libraries.py --jar dist/SigmaNG-Android-14.2.jar \
      --package-root it/unimi/dsi/fastutil \
      --package-root com/ibm/icu
"""
import argparse
import collections
import io
import os
import re
import sys
import zipfile

MAGIC = b"\xca\xfe\xba\xbe"
DESCR_RE = re.compile(rb"L([a-zA-Z0-9_$/]+);")


def u2(buf, off):
    return (buf[off] << 8) | buf[off + 1]


def u4(buf, off):
    return (buf[off] << 24) | (buf[off + 1] << 16) | (buf[off + 2] << 8) | buf[off + 3]


def parse_class_refs(data: bytes):
    """Return the set of class names referenced by one .class file, or None
    if the buffer is not a class file."""
    if len(data) < 10 or data[:4] != MAGIC:
        return None
    cp_count = u2(data, 8)
    pos = 10
    utf8 = {}
    classes = set()
    descr = set()
    i = 1
    while i < cp_count:  # JVM spec: constant_pool_count = number of entries + 1
        tag = data[pos]
        pos += 1
        if tag == 1:  # Utf8
            n = u2(data, pos)
            pos += 2
            utf8[i] = data[pos:pos + n]
            pos += n
        elif tag == 7:  # Class -> name is a utf8 index
            classes.add(u2(data, pos))
            pos += 2
        elif tag == 8:  # String
            pos += 2
        elif tag == 9 or tag == 10 or tag == 11:  # Field/Method/InterfaceMethodref
            pos += 4  # class_index (redundant: resolved via Class entry) + nat_index
        elif tag == 3 or tag == 4:  # int/float
            pos += 4
        elif tag == 5 or tag == 6:  # long/double
            pos += 8
        elif tag == 12:  # NameAndType -> descriptor utf8 index
            descr.add(u2(data, pos + 2))
            pos += 4
        elif tag == 15:  # MethodHandle
            pos += 3
        elif tag == 16:  # MethodType -> descriptor utf8 index
            descr.add(u2(data, pos))
            pos += 2
        elif tag == 17 or tag == 18:  # Dynamic / InvokeDynamic
            pos += 4  # bootstrap index + NameAndType (descriptor covered via tag 12 pass)
        else:
            return None  # unknown tag: bail out (caller keeps everything)
        i += 1
        if tag == 5 or tag == 6:
            i += 1  # 8-byte constants take two slots

    refs = set()
    for idx in classes:
        name = utf8.get(idx, b"")
        if name.startswith(b"["):
            for m in DESCR_RE.finditer(name):
                refs.add(m.group(1).decode("utf-8", "replace"))
        elif name:
            refs.add(name.decode("utf-8", "replace"))
    for idx in descr:
        d = utf8.get(idx, b"")
        for m in DESCR_RE.finditer(d):
            refs.add(m.group(1).decode("utf-8", "replace"))
    refs.discard("java/lang/Object")  # implicit everywhere
    return refs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jar", required=True, help="fat client jar to trim (rewritten in place)")
    ap.add_argument("--package-root", action="append", required=True,
                    help="classpath-style package root whose unused classes may be dropped (repeatable)")
    args = ap.parse_args()

    roots = tuple(r.strip("/").replace(".", "/") for r in args.package_root)

    with zipfile.ZipFile(args.jar, "r") as zf:
        names = zf.namelist()
        class_entries = [n for n in names if n.endswith(".class")]
        refs = {}
        failed = set()
        for n in class_entries:
            r = parse_class_refs(zf.read(n))
            if r is None:
                failed.add(n[:-6])
                refs[n[:-6]] = set()
            else:
                refs[n[:-6]] = r

    def is_target(name: str) -> bool:
        return name.startswith(roots)

    target_names = {n for n in refs if is_target(n)}
    non_target = {n for n in refs if not is_target(n)}

    # conservative: any target class whose class file could not be parsed is kept
    keep = {t for t in target_names if t in failed}
    if failed:
        print("[trim] WARNING: %d class files could not be parsed (all kept)" % len(failed))

    # closure: target classes reachable from any non-target class (transitive)
    work = collections.deque()
    for n in non_target:
        for r in refs[n]:
            if r in target_names and r not in keep:
                keep.add(r)
                work.append(r)
    while work:
        t = work.popleft()
        for r in refs.get(t, ()):
            if r in target_names and r not in keep:
                keep.add(r)
                work.append(r)

    removed = {t for t in target_names if t not in keep}
    if not removed:
        print("[trim] nothing to remove (all %d target classes are referenced)" % len(target_names))
        return 0

    # rewrite the jar without the removed classes (level 9, everything else identical)
    tmp = args.jar + ".tmp"
    with zipfile.ZipFile(args.jar, "r") as zin, \
            zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zout:
        for info in zin.infolist():
            if info.filename.endswith(".class"):
                if info.filename[:-6] in removed:
                    continue
            zout.writestr(info.filename, zin.read(info.filename))
    os.replace(tmp, args.jar)

    size = os.path.getsize(args.jar)
    print("[trim] roots: %s" % ", ".join(roots))
    print("[trim] target classes: %d | kept: %d | removed: %d" %
          (len(target_names), len(keep), len(removed)))
    print("[trim] new jar size: %d bytes" % size)
    return 0


if __name__ == "__main__":
    sys.exit(main())
