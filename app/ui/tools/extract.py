#!/usr/bin/env python3
"""Decode a __bundler HTML export as DATA (no script execution).

Usage: extract.py <original.html> <outdir>

Reads the four `<script type="__bundler/*">` islands, base64-decodes and
gunzips every manifest entry, and writes the decoded tree plus an
inventory. Nothing from the artifact is executed.
"""
import base64
import gzip
import hashlib
import html
import json
import mimetypes
import os
import re
import sys

EXT_BY_MIME = {
    "text/html": ".html",
    "text/css": ".css",
    "text/javascript": ".js",
    "application/javascript": ".js",
    "application/json": ".json",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/svg+xml": ".svg",
    "image/webp": ".webp",
    "font/woff2": ".woff2",
    "font/woff": ".woff",
    "font/ttf": ".ttf",
    "font/otf": ".otf",
    "application/x-font-ttf": ".ttf",
    "text/plain": ".txt",
}

KIND_BY_MIME = [
    (re.compile(r"^font/|^application/(x-)?font-|vnd\.ms-fontobject"), "font"),
    (re.compile(r"^image/"), "image"),
    (re.compile(r"^text/css"), "css"),
    (re.compile(r"^(text|application)/(java|ecma)script"), "script"),
    (re.compile(r"^application/json"), "data"),
    (re.compile(r"^text/html"), "page"),
]


def kind_for(mime):
    for rx, k in KIND_BY_MIME:
        if rx.search(mime or ""):
            return k
    return "data"


def island(src, name):
    """Return the raw text of <script type="__bundler/<name>">...</script>."""
    m = re.search(
        r'<script type="__bundler/%s">(.*?)</script>' % re.escape(name),
        src,
        re.S,
    )
    return m.group(1) if m else None


def safe_name(s):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", s)[:120]


def extract(src_path, out):
    src = open(src_path, "r", encoding="utf-8").read()

    os.makedirs(out, exist_ok=True)
    steps = []
    steps.append(("read", src_path, len(src)))

    manifest = json.loads(island(src, "manifest"))
    ext_resources = json.loads(island(src, "ext_resources"))
    page_order = json.loads(island(src, "page_order"))
    template = json.loads(island(src, "template"))  # JSON-encoded string

    # uuid -> logical id from the ext_resources manifest
    id_by_uuid = {}
    for e in ext_resources:
        id_by_uuid.setdefault(e["uuid"], []).append(e["id"])

    res_dir = os.path.join(out, "resources")
    os.makedirs(res_dir, exist_ok=True)

    inventory = []
    for uuid, entry in manifest.items():
        raw = base64.b64decode(entry["data"])
        b64_len = len(entry["data"])
        data = gzip.decompress(raw) if entry.get("compressed") else raw
        mime = entry.get("mime", "")
        ids = id_by_uuid.get(uuid, [])
        label = ids[0] if ids else uuid
        kind = "page" if uuid in page_order else kind_for(mime)
        ext = EXT_BY_MIME.get(mime) or mimetypes.guess_extension(mime) or ".bin"
        base = safe_name(os.path.basename(label.rstrip("/")) or uuid)
        if not base.endswith(ext):
            base = base + ext
        # keep uuid prefix so collisions cannot occur
        fname = "%s__%s" % (uuid[:8], base)
        path = os.path.join(res_dir, fname)
        with open(path, "wb") as fh:
            fh.write(data)
        inventory.append(
            {
                "uuid": uuid,
                "ids": ids,
                "mime": mime,
                "kind": kind,
                "compressed": bool(entry.get("compressed")),
                "b64_len": b64_len,
                "gz_bytes": len(raw),
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "file": os.path.relpath(path, out),
            }
        )
        steps.append(("decode", uuid, label, mime, len(data)))

    # The template as shipped (uuid placeholders intact)
    tpl_path = os.path.join(out, "template.raw.html")
    with open(tpl_path, "w", encoding="utf-8") as fh:
        fh.write(template)

    # A readable rewrite: uuid -> resources/<file>, so the template can be
    # inspected (and later served) as a normal source tree.
    rewritten = template
    for row in inventory:
        rewritten = rewritten.replace(row["uuid"], row["file"])
    with open(os.path.join(out, "template.resolved.html"), "w", encoding="utf-8") as fh:
        fh.write(rewritten)

    # Split the template's inline <script>/<style> blocks out as source files.
    src_dir = os.path.join(out, "template_parts")
    os.makedirs(src_dir, exist_ok=True)
    n = 0
    for m in re.finditer(r"<script([^>]*)>(.*?)</script>", template, re.S):
        attrs, body = m.group(1), m.group(2)
        if not body.strip():
            continue
        n += 1
        t = re.search(r'type="([^"]+)"', attrs)
        t = t.group(1) if t else "text/javascript"
        ext = ".jsx" if "babel" in t or "jsx" in t else ".js"
        with open(os.path.join(src_dir, "inline_%02d%s" % (n, ext)), "w", encoding="utf-8") as fh:
            fh.write("// type=%s\n" % t)
            fh.write(html.unescape(body))
    n = 0
    for m in re.finditer(r"<style[^>]*>(.*?)</style>", template, re.S):
        n += 1
        with open(os.path.join(src_dir, "inline_%02d.css" % n), "w", encoding="utf-8") as fh:
            fh.write(m.group(1))

    # The <x-dc> template markup on its own (design + directives), with the
    # <helmet> style island and the logic script removed.
    xdc = re.search(r"<x-dc[^>]*>(.*)</x-dc>", template, re.S)
    if xdc:
        markup = re.sub(r"<helmet>.*?</helmet>", "", xdc.group(1), flags=re.S)
        markup = re.sub(r"<script.*?</script>", "", markup, flags=re.S)
        with open(os.path.join(src_dir, "markup.html"), "w", encoding="utf-8") as fh:
            fh.write(markup)

    with open(os.path.join(out, "manifest.inventory.json"), "w", encoding="utf-8") as fh:
        json.dump(
            {
                "source": src_path,
                "source_sha256": hashlib.sha256(
                    open(src_path, "rb").read()
                ).hexdigest(),
                "source_bytes": os.path.getsize(src_path),
                "page_order": page_order,
                "ext_resources": ext_resources,
                "resources": inventory,
                "template_bytes": len(template),
                "template_sha256": hashlib.sha256(template.encode()).hexdigest(),
            },
            fh,
            indent=2,
        )

    print("== %s -> %s" % (src_path, out))
    print("resources decoded:", len(inventory), "| template bytes:", len(template))
    for row in sorted(inventory, key=lambda r: -r["bytes"]):
        print(
            "%-10s %-28s %-24s %9d  %s"
            % (row["kind"], (row["ids"] or [row["uuid"]])[0][:28], row["mime"], row["bytes"], row["file"])
        )

    # Nested bundles: any decoded text/html resource that is itself a
    # __bundler export (the JIPOE map is one). Recurse as DATA.
    for row in inventory:
        if row["kind"] != "page" and not row["mime"].startswith("text/html"):
            continue
        p = os.path.join(out, row["file"])
        head = open(p, "r", encoding="utf-8", errors="replace").read(4000)
        if '__bundler/manifest' not in head and 'type="__bundler' not in head:
            continue
        label = safe_name((row["ids"] or [row["uuid"][:8]])[0])
        extract(p, os.path.join(out, label))


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: extract.py <original.html> <outdir>")
    src_path = os.path.abspath(os.path.expanduser(sys.argv[1]))
    out = os.path.abspath(os.path.expanduser(sys.argv[2]))
    extract(src_path, out)


if __name__ == "__main__":
    main()
