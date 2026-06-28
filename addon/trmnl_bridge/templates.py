"""Discovery of the bundled (and user-supplied) Liquid templates for the panel.

The template folders are scanned dynamically, so dropping a new ``.liquid`` file
(plus a ``templates.yaml`` entry) into ``/data/templates`` makes it appear in
the panel — not limited to weather use cases.
"""

from __future__ import annotations

import os

from .constants import TEMPLATE_DIRS
from .formatting import titleize

try:
    import yaml
except ImportError:  # PyYAML ships in the add-on image; optional elsewhere.
    yaml = None

_TPL_BEGIN = "<!-- BEGIN extension content -->"
_TPL_END = "<!-- END extension content -->"


def _template_inner(text: str) -> str:
    """The content between the BEGIN/END markers — what you paste into a
    Terminus extension's editor. (Matches the full HTML-comment markers so the
    header comment's mention of the words doesn't trip it up.)"""
    b = text.find(_TPL_BEGIN)
    e = text.find(_TPL_END)
    if b == -1 or e == -1:
        return text.strip()
    return text[b + len(_TPL_BEGIN):e].strip("\n")


def _read_template_meta(directory: str) -> list[dict]:
    """Ordered metadata from a folder's templates.yaml (empty if absent).

    Any parse error (or PyYAML being unavailable) degrades to no metadata —
    templates still appear, just with filename-derived labels.
    """
    if yaml is None:
        return []
    try:
        with open(os.path.join(directory, "templates.yaml"),
                  "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except (OSError, yaml.YAMLError):
        return []
    if not isinstance(data, dict):
        return []
    return [m for m in data.get("templates", []) if isinstance(m, dict)]


def load_templates() -> list[dict]:
    """Every *.liquid in the template folders (bundled + an optional
    /data/templates overlay), as paste-ready snippets described by each folder's
    templates.yaml. The folder is scanned dynamically, so dropping in a new
    template makes it appear in the panel — not limited to weather use cases."""
    out, seen = [], set()
    for directory in TEMPLATE_DIRS:
        if not os.path.isdir(directory):
            continue
        meta_list = _read_template_meta(directory)
        meta_by_file = {m.get("file"): m for m in meta_list if m.get("file")}
        files = sorted(f for f in os.listdir(directory)
                       if f.endswith(".liquid") and not f.startswith("_"))
        order = [m["file"] for m in meta_list if m.get("file") in files]
        order += [f for f in files if f not in order]
        for fname in order:
            if fname in seen:
                continue
            try:
                with open(os.path.join(directory, fname),
                          "r", encoding="utf-8") as fh:
                    text = fh.read()
            except OSError:
                continue
            seen.add(fname)
            m = meta_by_file.get(fname, {})
            name = fname[:-len(".liquid")]
            out.append({
                "name": name, "file": fname,
                "label": m.get("label") or titleize(name),
                "size": m.get("size", ""),
                "category": m.get("category", ""),
                "description": m.get("description", ""),
                "content": _template_inner(text),
            })
    return out
