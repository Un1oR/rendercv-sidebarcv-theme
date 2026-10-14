"""Render public examples in a clean consumer directory and compare PNGs.

Baseline writes require an explicit command: python -m tests.visual --update.
"""

import argparse
from html import unescape
import importlib.metadata
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

from PIL import Image, ImageChops, ImageEnhance
import rendercv_fonts
from ruamel.yaml import YAML
import typst
from rendercv.renderer.pdf_png import get_package_path

from tests.support import ROOT, OUTPUT


EXAMPLES = ("starter", "john", "alice", "bob")
BASELINES = Path(__file__).parent / "baselines"
PPI = 144
CURRENT_DATE = "2026-10-14"
MAX_CHANNEL_DELTA = 2
VERSIONS = {"rendercv": "2.8", "typst": "0.15.0", "rendercv-fonts": "0.5.1"}


def environment():
    versions = {name: importlib.metadata.version(name) for name in VERSIONS}
    if versions != VERSIONS:
        raise AssertionError(f"Install the pinned dev dependencies: expected {VERSIONS}, got {versions}")
    return {"versions": versions, "ppi": PPI, "current_date": CURRENT_DATE}


def compare_page(expected, actual, report):
    """Reject every pixel with a channel difference > 2, without alignment or blur."""
    with Image.open(expected) as source, Image.open(actual) as rendered:
        before, after = source.convert("RGB"), rendered.convert("RGB")
    if before.size != after.size:
        raise AssertionError(f"Page size changed: {before.size} -> {after.size}; actual: {actual}")
    difference = ImageChops.difference(before, after)
    largest_delta = max(channel[1] for channel in difference.getextrema())
    if largest_delta <= MAX_CHANNEL_DELTA:
        return
    report.parent.mkdir(parents=True, exist_ok=True)
    ImageEnhance.Contrast(difference).enhance(4).save(report)
    histogram = ImageChops.lighter(
        ImageChops.lighter(*difference.split()[:2]), difference.split()[2]
    ).histogram()
    changed = sum(histogram[MAX_CHANNEL_DELTA + 1:])
    raise AssertionError(
        f"{changed} pixels exceed ±{MAX_CHANNEL_DELTA}/255 (max {largest_delta}); "
        f"expected: {expected}; actual: {actual}; difference: {report}"
    )


def _plain(value):
    value = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", str(value))
    return " ".join(unescape(value).replace("*", "").replace("`", "").split())


def check_content(data, markdown, html):
    """Standard body fields survive the unstyled Markdown and HTML pipeline."""
    plain_markdown = _plain(markdown)
    plain_html = _plain(re.sub(r"<[^>]+>", "", html))
    values = [data["cv"]["name"]]
    for entries in data["cv"]["sections"].values():
        for entry in entries:
            if isinstance(entry, str):
                values.append(entry)
                continue
            for key, value in entry.items():
                if value is None:
                    continue
                if key in {"name", "company", "position", "institution", "area", "degree",
                           "title", "label", "details", "summary", "bullet", "number", "reversed_number"}:
                    values.append(value)
                elif key == "highlights":
                    # RenderCV turns inline " - " into nested highlight items.
                    values.extend(part for highlight in value for part in highlight.split(" - "))
                elif key == "authors":
                    values.extend(value)
    for value in values:
        text = _plain(value)
        for format_name, output in [("Markdown", plain_markdown), ("HTML", plain_html)]:
            if text not in output:
                raise AssertionError(f"{format_name} lost content: {value!r}")


def render_example(name):
    """Exercise the documented directory-based installation through the real CLI."""
    environment()
    consumer = OUTPUT / "visual" / name
    if consumer.exists():
        shutil.rmtree(consumer)
    consumer.mkdir(parents=True)
    shutil.copytree(ROOT / "sidebarcv", consumer / "sidebarcv",
                    ignore=shutil.ignore_patterns("__pycache__", "fonts"))
    source = consumer / "cv.yaml"
    shutil.copyfile(ROOT / "examples" / f"{name}.yaml", source)
    data = YAML(typ="safe").load(source)
    photo = data.get("cv", {}).get("photo")
    if photo and not photo.startswith(("http://", "https://")):
        (consumer / photo).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / "examples" / photo, consumer / photo)
    result = subprocess.run([
        sys.executable, "-m", "rendercv", "render", str(source),
        "--dont-generate-png",
        "--settings.current_date", CURRENT_DATE,
    ], cwd=consumer, capture_output=True, text=True, timeout=120)
    (consumer / "cli.log").write_text(result.stdout + result.stderr)
    if result.returncode:
        raise AssertionError(f"RenderCV CLI failed for {name}:\n{result.stdout}\n{result.stderr}")
    generated = consumer / "rendercv_output"
    for extension in ["pdf", "typ", "md", "html"]:
        if len(list(generated.glob(f"*.{extension}"))) != 1:
            raise AssertionError(f"Expected one {extension} output in {generated}")
    check_content(data, next(generated.glob("*.md")).read_text(), next(generated.glob("*.html")).read_text())
    compiler = typst.Compiler(
        root=consumer, font_paths=rendercv_fonts.paths_to_font_folders,
        ignore_system_fonts=True, package_path=get_package_path(),
    )
    pages = compiler.compile(input=next(generated.glob("*.typ")), format="png", ppi=PPI)
    if isinstance(pages, bytes):
        pages = [pages]
    paths = []
    for number, page in enumerate(pages, 1):
        path = generated / f"page-{number}.png"
        path.write_bytes(page)
        paths.append(path)
    return paths


def check_example(name, update=False):
    actual = render_example(name)
    baseline = BASELINES / name
    if update:
        baseline.mkdir(parents=True, exist_ok=True)
        for previous in baseline.glob("page-*.png"):
            previous.unlink()
        for path in actual:
            shutil.copyfile(path, baseline / path.name)
        (baseline / "environment.json").write_text(json.dumps(environment(), indent=2) + "\n")
        return
    manifest = baseline / "environment.json"
    if not manifest.exists():
        raise AssertionError(f"Missing baseline for {name}; inspect renders, then run python -m tests.visual --update {name}")
    if json.loads(manifest.read_text()) != environment():
        raise AssertionError(f"Baseline environment changed; review {manifest}")
    expected = sorted(baseline.glob("page-*.png"))
    if {path.name for path in expected} != {path.name for path in actual}:
        raise AssertionError(f"Page count changed for {name}: {len(expected)} -> {len(actual)}; inspect {actual[0].parent}")
    for rendered in actual:
        compare_page(baseline / rendered.name, rendered, rendered.with_name(f"diff-{rendered.name}"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--update", action="store_true", help="Explicitly replace reviewed PNG baselines")
    parser.add_argument("examples", nargs="*", choices=EXAMPLES)
    args = parser.parse_args()
    for example in args.examples or EXAMPLES:
        check_example(example, update=args.update)
        print(f"{example}: {'updated' if args.update else 'passed'}")
