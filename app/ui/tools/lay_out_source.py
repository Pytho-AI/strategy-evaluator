#!/usr/bin/env python3
"""Lay the decoded __bundler tree out as an ordinary static source tree.

Usage: lay_out_source.py <decoded-dir> <outdir>

`<decoded-dir>` is what tools/extract.py produced. This script only moves and
renames files and rewrites resource references (uuid -> relative path). It makes
no behavioural change to the recovered markup or logic; the small semantic edits
applied on top of its output are listed in app/ui/RECOVERY.md.

Re-run it into a scratch directory and diff against app/ui to see exactly which
files carry a hand edit.
"""
import hashlib
import json
import os
import re
import shutil
import sys

# The three <style> islands in the template, in document order.
STYLE_FILES = [
    ("inline_01.css", "src/styles/01-industry-tokens.css"),
    ("inline_02.css", "src/styles/02-source-sans-3.css"),
    ("inline_03.css", "src/styles/03-app-overrides.css"),
]

# Root-bundle scripts, by the decoded filename prefix extract.py assigns.
VENDOR = {
    "15a49b3a": "vendor/dc-runtime.js",
    "296a0e32": "vendor/react.production.min.js",
    "9b33a968": "vendor/react-dom.production.min.js",
    "97ceecaa": "vendor/ds-bundle-industry.js",
    "0d967fce": "assets/docreader.js",
}

# jipoeMap-bundle scripts and data.
MAP_VENDOR = {
    "8b0e78de": "vendor/d3.v7.9.0.min.js",
    "e498e85a": "vendor/topojson-client.v3.1.0.min.js",
    "927c98b3": "data/countries-110m.json",
}

FONT_FACE_RE = re.compile(
    r"(?:/\*\s*([^*]+?)\s*\*/\s*)?@font-face\s*\{(.*?)\}", re.S
)


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def font_names(css_texts):
    """uuid -> 'barlow-400-latin.woff2', derived from the @font-face rules.

    Source Sans 3 declares 400/500/600/700 over the same seven subset files, so
    the weight is dropped from the name whenever one file serves more than one
    weight.
    """
    faces = []
    for css in css_texts:
        for comment, body in FONT_FACE_RE.findall(css):
            fam = re.search(r"font-family:\s*['\"]([^'\"]+)", body)
            wgt = re.search(r"font-weight:\s*(\d+)", body)
            sty = re.search(r"font-style:\s*(\w+)", body)
            url = re.search(r"url\(\s*['\"]([^'\"]+)['\"]", body)
            if not (fam and url):
                continue
            faces.append((url.group(1), fam.group(1),
                          wgt.group(1) if wgt else "400",
                          sty.group(1) if sty else "normal",
                          comment or "latin"))
    weights = {}
    for uuid, _fam, wgt, _sty, _sub in faces:
        weights.setdefault(uuid, set()).add(wgt)
    names = {}
    for uuid, fam, wgt, sty, sub in faces:
        parts = [slug(fam)]
        if len(weights[uuid]) == 1:
            parts.append(wgt)
        if sty != "normal":
            parts.append(sty)
        parts.append(slug(sub))
        names[uuid] = "-".join(parts) + ".woff2"
    return names


def sha256(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def lay_out_map(decoded, out, rows):
    """assets/jipoe-map/ — the nested bundle as a plain static page."""
    src = os.path.join(decoded, "jipoeMap")
    dst = os.path.join(out, "assets/jipoe-map")
    inv = json.load(open(os.path.join(src, "manifest.inventory.json")))
    css = [open(os.path.join(src, "template_parts", n)).read()
           for n in ("inline_01.css", "inline_02.css")]
    fonts = font_names(css)

    dest_by_uuid = {}
    for row in inv["resources"]:
        pfx = os.path.basename(row["file"]).split("__")[0]
        if pfx in MAP_VENDOR:
            rel = MAP_VENDOR[pfx]
        else:
            rel = "fonts/" + fonts[(row["ids"] or [row["uuid"]])[0]]
        dest_by_uuid[row["uuid"]] = rel
        target = os.path.join(dst, rel)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copyfile(os.path.join(src, row["file"]), target)
        rows.append(("jipoe-map", row, "assets/jipoe-map/" + rel))

    page = open(os.path.join(src, "template.raw.html")).read()
    for uuid, rel in dest_by_uuid.items():
        page = page.replace(uuid, rel)
    with open(os.path.join(dst, "index.html"), "w") as fh:
        fh.write(page)


def lay_out(decoded, out):
    inv = json.load(open(os.path.join(decoded, "manifest.inventory.json")))
    parts = os.path.join(decoded, "template_parts")
    css = [open(os.path.join(parts, n)).read() for n, _ in STYLE_FILES]
    fonts = font_names(css)

    rows = []
    dest_by_uuid = {}
    for row in inv["resources"]:
        pfx = os.path.basename(row["file"]).split("__")[0]
        if pfx in VENDOR:
            rel = VENDOR[pfx]
        elif row["kind"] == "font":
            rel = "assets/fonts/" + fonts[(row["ids"] or [row["uuid"]])[0]]
        elif row["kind"] == "page":
            rel = "assets/jipoe-map/index.html"  # unbundled below
        else:
            raise SystemExit("unmapped resource: %r" % row)
        dest_by_uuid[row["uuid"]] = rel
        if row["kind"] != "page":
            target = os.path.join(out, rel)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.copyfile(os.path.join(decoded, row["file"]), target)
        rows.append(("root", row, rel))

    # Styles: same bytes, with the uuid font references rewritten to ../../assets/fonts.
    for name, rel in STYLE_FILES:
        text = open(os.path.join(parts, name)).read()
        for uuid, dest in dest_by_uuid.items():
            if dest.startswith("assets/fonts/"):
                text = text.replace(uuid, "../../" + dest)
        target = os.path.join(out, rel)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w") as fh:
            fh.write(text)

    # Markup and logic, verbatim from the decoded template parts.
    os.makedirs(os.path.join(out, "src"), exist_ok=True)
    shutil.copyfile(os.path.join(parts, "markup.html"),
                    os.path.join(out, "src/app.dc.html"))
    logic = open(os.path.join(parts, "inline_01.js")).read()
    logic = logic.replace("// type=text/x-dc\n", "", 1).lstrip("\n")
    with open(os.path.join(out, "src/app.logic.js"), "w") as fh:
        fh.write(logic)

    # The editor-facing prop schema, lifted off the data-props attribute.
    raw = open(os.path.join(decoded, "template.raw.html")).read()
    props = re.search(r'data-props="([^"]*)"', raw).group(1)
    props = (props.replace("&quot;", '"').replace("&amp;", "&")
             .replace("&lt;", "<").replace("&gt;", ">"))
    with open(os.path.join(out, "src/app.props.json"), "w") as fh:
        json.dump(json.loads(props), fh, indent=2)
        fh.write("\n")

    lay_out_map(decoded, out, rows)
    return rows


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: lay_out_source.py <decoded-dir> <outdir>")
    decoded, out = (os.path.abspath(os.path.expanduser(a)) for a in sys.argv[1:3])
    rows = lay_out(decoded, out)
    print("| bundle | id | kind | bytes | sha256 | destination |")
    print("|---|---|---|---|---|---|")
    for bundle, row, rel in sorted(rows, key=lambda r: (r[0], r[2])):
        print("| %s | `%s` | %s | %d | `%s` | `%s` |" % (
            bundle, (row["ids"] or [row["uuid"]])[0], row["kind"],
            row["bytes"], row["sha256"], rel))


if __name__ == "__main__":
    main()
