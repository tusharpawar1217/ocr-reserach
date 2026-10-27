#!/usr/bin/env python3
"""
sort_images_by_resolution.py

Sorts images in a folder into High / Medium / Low resolution buckets,
based on total megapixels (width x height).

Usage:
    python3 sort_images_by_resolution.py /path/to/source_folder

Optional flags:
    --mode copy|move      (default: copy)  -> copy or move files into buckets
    --dest /path/to/out    (default: <source>/sorted_by_resolution)
    --high 2.0             (default: 2.0)  -> MP threshold for High (>=)
    --medium 0.3            (default: 0.3) -> MP threshold for Medium (>=)
                                              anything below goes to Low
    --report                                -> also write a CSV report

Handles all common image extensions: jpg, jpeg, png, bmp, gif, tiff, tif,
webp, heic, heif, ico, ppm, pgm, pbm, jfif (anything Pillow can open).
"""

import argparse
import csv
import shutil
import sys
from pathlib import Path

from PIL import Image, UnidentifiedImageError

# Common image extensions Pillow can typically read.
# We don't filter strictly by extension - we try to open every file and
# skip ones that fail, so this list is just a fast pre-filter.
IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".jfif", ".png", ".bmp", ".gif", ".tif", ".tiff",
    ".webp", ".heic", ".heif", ".ico", ".ppm", ".pgm", ".pbm", ".tga",
}


def get_category(width: int, height: int, high_mp: float, medium_mp: float) -> str:
    mp = (width * height) / 1_000_000  # megapixels
    if mp >= high_mp:
        return "high"
    elif mp >= medium_mp:
        return "medium"
    else:
        return "low"


def collect_image_files(source: Path):
    """Return all files under source whose extension looks like an image."""
    files = []
    for p in source.rglob("*"):
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS:
            files.append(p)
    return files


def main():
    parser = argparse.ArgumentParser(description="Sort images by resolution into high/medium/low folders.")
    parser.add_argument("source", type=str, help="Path to the folder containing images")
    parser.add_argument("--mode", choices=["copy", "move"], default="copy",
                         help="Copy or move files into resolution folders (default: copy)")
    parser.add_argument("--dest", type=str, default=None,
                         help="Destination root folder (default: <source>/sorted_by_resolution)")
    parser.add_argument("--high", type=float, default=2.0,
                         help="Megapixel threshold for 'high' (default: 2.0 MP, e.g. ~1920x1080)")
    parser.add_argument("--medium", type=float, default=0.3,
                         help="Megapixel threshold for 'medium' (default: 0.3 MP, e.g. ~640x480)")
    parser.add_argument("--report", action="store_true",
                         help="Also write a CSV report (image_resolution_report.csv) in the dest folder")
    args = parser.parse_args()

    source = Path(args.source).expanduser().resolve()
    if not source.is_dir():
        print(f"Error: source folder does not exist: {source}")
        sys.exit(1)

    dest_root = Path(args.dest).expanduser().resolve() if args.dest else source / "sorted_by_resolution"
    high_dir = dest_root / "high"
    medium_dir = dest_root / "medium"
    low_dir = dest_root / "low"
    for d in (high_dir, medium_dir, low_dir):
        d.mkdir(parents=True, exist_ok=True)

    files = collect_image_files(source)
    # Don't re-process files that already live inside the destination folder
    files = [f for f in files if dest_root not in f.parents]

    if not files:
        print(f"No image files found under: {source}")
        sys.exit(0)

    print(f"Found {len(files)} image file(s). Scanning resolutions...\n")

    report_rows = []
    counts = {"high": 0, "medium": 0, "low": 0}
    skipped = []

    for path in files:
        try:
            with Image.open(path) as img:
                width, height = img.size
        except (UnidentifiedImageError, OSError) as e:
            skipped.append((path, str(e)))
            continue

        category = get_category(width, height, args.high, args.medium)
        counts[category] += 1

        target_dir = {"high": high_dir, "medium": medium_dir, "low": low_dir}[category]
        target_path = target_dir / path.name

        # Avoid overwriting files with the same name
        if target_path.exists():
            stem, suffix = target_path.stem, target_path.suffix
            i = 1
            while target_path.exists():
                target_path = target_dir / f"{stem}_{i}{suffix}"
                i += 1

        if args.mode == "copy":
            shutil.copy2(path, target_path)
        else:
            shutil.move(str(path), str(target_path))

        mp = (width * height) / 1_000_000
        report_rows.append([path.name, width, height, f"{mp:.2f}", category])
        print(f"  {path.name:40s} {width}x{height} ({mp:.2f} MP) -> {category}")

    if args.report:
        report_path = dest_root / "image_resolution_report.csv"
        with open(report_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["filename", "width", "height", "megapixels", "category"])
            writer.writerows(report_rows)
        print(f"\nCSV report written to: {report_path}")

    print("\nDone.")
    print(f"  High:   {counts['high']}")
    print(f"  Medium: {counts['medium']}")
    print(f"  Low:    {counts['low']}")
    if skipped:
        print(f"  Skipped (unreadable): {len(skipped)}")
        for p, err in skipped:
            print(f"    - {p.name}: {err}")


if __name__ == "__main__":
    main()