#!/usr/bin/env python3
"""Sanity-check a design spec YAML before handing it to developers.

Usage: python validate_spec.py spec.yaml

Checks: required top-level keys, every color/font referenced by a node exists
in tokens, every node has a tag, copy strings are non-empty, hex colors are
well-formed. Exits non-zero on errors; warnings are printed but do not fail.
Requires PyYAML.
"""
import re
import sys

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML is required: pip install pyyaml --break-system-packages")

HEX = re.compile(r"^#[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?$")
REQUIRED_TOP = ["meta", "tokens", "layout", "structure", "copy"]
VOID_TAGS = {"img", "input", "br", "hr"}

errors, warnings = [], []


def walk(node, path, color_names, font_names, copy_ids):
    if not isinstance(node, dict):
        errors.append(f"{path}: node must be a mapping")
        return
    tag = node.get("tag")
    if not tag:
        errors.append(f"{path}: missing `tag`")
    if tag == "div" and not node.get("role") and not node.get("note"):
        warnings.append(f"{path}: <div> with no role/note — is there a more semantic tag?")
    if tag == "img" and not node.get("alt"):
        warnings.append(f"{path}: <img> without alt")
    if tag in ("a", "button") and not (node.get("copy") or node.get("aria_label")):
        warnings.append(f"{path}: interactive element with no copy or aria_label")
    for key in ("color", "background", "border_color"):
        v = (node.get("style") or {}).get(key)
        if v and not v.startswith("#") and v not in color_names:
            errors.append(f"{path}: style.{key} references unknown color token `{v}`")
    fnt = (node.get("style") or {}).get("font")
    if fnt and fnt not in font_names:
        errors.append(f"{path}: style.font references unknown font token `{fnt}`")
    cp = node.get("copy")
    if cp and cp not in copy_ids:
        errors.append(f"{path}: copy id `{cp}` not found in top-level `copy`")
    if tag in VOID_TAGS and node.get("children"):
        errors.append(f"{path}: void element <{tag}> cannot have children")
    for i, child in enumerate(node.get("children") or []):
        walk(child, f"{path}.children[{i}]", color_names, font_names, copy_ids)


def main(path):
    with open(path) as f:
        spec = yaml.safe_load(f)
    for k in REQUIRED_TOP:
        if k not in spec:
            errors.append(f"missing top-level key `{k}`")
    if errors:
        report(); return

    colors = spec["tokens"].get("colors") or {}
    fonts = spec["tokens"].get("fonts") or {}
    for name, c in colors.items():
        val = c["value"] if isinstance(c, dict) else c
        if not HEX.match(str(val)):
            errors.append(f"tokens.colors.{name}: `{val}` is not a #RRGGBB hex")
    for cid, entry in (spec.get("copy") or {}).items():
        text = entry["text"] if isinstance(entry, dict) else entry
        if not str(text).strip():
            errors.append(f"copy.{cid}: empty text")
    if "confidence" not in spec["meta"]:
        warnings.append("meta.confidence missing — devs should know how sure the extraction is")

    for i, node in enumerate(spec["structure"] or []):
        walk(node, f"structure[{i}]", set(colors), set(fonts), set(spec.get("copy") or {}))
    report()


def report():
    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
