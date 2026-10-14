"""Rebuild checked-in gallery assets with the project's RenderCV environment."""

from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont
from ruamel.yaml import YAML


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "assets"
# Identical 144-dpi sidebar regions preserve the context and the real whitespace.
PAGINATION_CROPS = ((800, 1080, 1132, 1484), (800, 84, 1132, 294))


def page_pngs(pdf):
    """Select rendered pages, excluding a photo copied beside the Typst source."""
    pattern = re.compile(re.escape(pdf.stem) + r"_([1-9][0-9]*)\.png")
    pages = [(int(match[1]), path) for path in pdf.parent.glob("*.png")
             if (match := pattern.fullmatch(path.name))]
    return [path for _, path in sorted(pages)]


def prepare_example(source, destination, *, hero=False):
    """The hero uses photo-free Alice with flowing sections; gallery inputs stay intact."""
    yaml = YAML()
    data = yaml.load(source)
    if hero:
        data["cv"].pop("photo", None)
        data["design"]["sections"]["overrides"]["skills"]["allow_page_break"] = True
        yaml.dump(data, destination)
    else:
        shutil.copy2(source, destination)
    photo = data.get("cv", {}).get("photo")
    if photo and not photo.startswith(("http://", "https://")):
        target = destination.parent / photo
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source.parent / photo, target)


def build_pagination_preview(mode):
    """Show identical sidebar regions on either side of the actual page break."""
    first_height, second_height = [box[3] - box[1] for box in PAGINATION_CROPS]
    second_top = first_height + 50
    preview = Image.new("RGB", (360, second_top + 27 + second_height), "#eaf0e8")
    draw = ImageDraw.Draw(preview)
    font = ImageFont.load_default(size=14)
    for number, box, top in [(1, PAGINATION_CROPS[0], 7), (2, PAGINATION_CROPS[1], second_top)]:
        draw.text((14, top), f"PAGE {number}", fill="#162d35", font=font)
        with Image.open(ASSETS / f"pagination-{mode}-{number}.png") as source:
            assert source.size == (1224, 1584), "Pagination crops require 144-dpi US-letter pages"
            preview.paste(source.convert("RGB").crop(box), (14, top + 20))
    seam_y = second_top - 9
    draw.line((14, seam_y, 346, seam_y), fill="#91a79b", width=1)
    draw.rectangle((138, seam_y - 6, 222, seam_y + 6), fill="#eaf0e8")
    draw.text((150, seam_y - 6), "PAGE BREAK", fill="#50656b", font=ImageFont.load_default(size=10))
    preview.save(ASSETS / f"pagination-{mode}.png", optimize=True)


def build_overview():
    """Compose the README preview from the actual first-page renderings."""
    overview = Image.new("RGB", (1600, 1260), "#eaf0e8")
    draw = ImageDraw.Draw(overview)
    draw.text((70, 42), "sidebarcv", fill="#162d35", font=ImageFont.load_default(size=54))
    draw.text((70, 110), "Independent columns. Familiar typography.", fill="#50656b", font=ImageFont.load_default(size=27))
    for x, name, title, description in [
        (70, "alice", "Alice Morgan", "Portrait / Compact header / Sidebar contacts"),
        (830, "bob", "Bob Ellis", "Wide sidebar / Centered header / Green palette"),
    ]:
        with Image.open(ASSETS / f"{name}-1.png") as source:
            page = source.convert("RGB")
            page.thumbnail((700, 940), Image.Resampling.LANCZOS)
            draw.rectangle((x + 7, 196, x + page.width + 7, 196 + page.height), fill="#d6dfd5")
            overview.paste(page, (x, 188))
        draw.text((x, 1120), title, fill="#162d35", font=ImageFont.load_default(size=27))
        draw.text((x, 1164), description, fill="#50656b", font=ImageFont.load_default(size=20))
    overview.save(ASSETS / "overview.png", optimize=True)


def main():
    ASSETS.mkdir(exist_ok=True)
    jobs = [(name, name, None) for name in ("starter", "john", "alice", "bob")]
    jobs.append(("hero", "alice", None))
    jobs += [
        ("comparison-before", "comparison", None),
        ("comparison-after", "comparison", "comparison-design.yaml"),
    ]
    jobs += [(f"pagination-{mode}", "pagination", f"pagination-{mode}.yaml")
             for mode in ("flow", "section", "groups")]
    with tempfile.TemporaryDirectory(prefix="sidebarcv-gallery-") as directory:
        for name, source, design in jobs:
            work = Path(directory) / name
            work.mkdir()
            shutil.copytree(ROOT / "sidebarcv", work / "sidebarcv")
            example = ROOT / "examples" / f"{source}.yaml"
            prepare_example(example, work / "cv.yaml", hero=name == "hero")
            command = [sys.executable, "-m", "rendercv", "render", "cv.yaml"]
            if design:
                shutil.copy2(ROOT / "examples" / design, work / "design.yaml")
                command += ["--design", "design.yaml"]
            subprocess.run(command, cwd=work, check=True)
            output = work / "rendercv_output"
            pdfs = list(output.glob("*.pdf"))
            # Fail loudly if rendering stops producing the documented examples.
            assert len(pdfs) == 1 and pdfs[0].read_bytes().startswith(b"%PDF-")
            pngs = page_pngs(pdfs[0])
            assert len(pngs) >= (2 if name in {"starter", "john", "alice", "bob"} else 1)
            if name.startswith("pagination-"):
                assert len(pngs) == 2, "Pagination comparison requires exactly two pages"
            assert all(path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n") for path in pngs)
            for old in ASSETS.glob(f"{name}-*.png"):
                if old.stem.removeprefix(f"{name}-").isdigit():
                    old.unlink()
            shutil.copy2(pdfs[0], ASSETS / f"{name}.pdf")
            for index, png in enumerate(pngs, 1):
                shutil.copy2(png, ASSETS / f"{name}-{index}.png")
            if name in {"starter", "john", "alice", "bob"}:
                html, = output.glob("*.html")
                shutil.copy2(html, ASSETS / f"{name}.html")
            print(f"{name}: {len(pngs)} page(s)")
    exposed_yaml = {f"{source}.yaml" for _, source, _ in jobs}
    exposed_yaml.update(design for _, _, design in jobs if design)
    for name in sorted(exposed_yaml):
        source = ROOT / "examples" / name
        shutil.copy2(source, ASSETS / name)
        photo = YAML(typ="safe").load(source).get("cv", {}).get("photo")
        if photo and not photo.startswith(("http://", "https://")):
            (ASSETS / photo).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source.parent / photo, ASSETS / photo)
    for mode in ("flow", "section", "groups"):
        build_pagination_preview(mode)
    build_overview()


if __name__ == "__main__":
    main()
