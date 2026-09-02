from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from PIL import Image


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: stitch_ancestry_tiles.py MANIFEST OUTPUT")

    manifest_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    tiles: list[tuple[int, int, Image.Image]] = []
    for asset in payload["assets"]:
        match = re.fullmatch(r"(\d+)_(\d+)\.jpg", asset["name"])
        if not match:
            continue
        x, y = (int(part) for part in match.groups())
        tiles.append((x, y, Image.open(asset["path"]).convert("RGB")))

    if not tiles:
        raise RuntimeError(f"no image tiles in {manifest_path}")

    tile_width = max(image.width for _, _, image in tiles)
    tile_height = max(image.height for _, _, image in tiles)
    max_x = max(x for x, _, _ in tiles)
    max_y = max(y for _, y, _ in tiles)
    canvas = Image.new("RGB", ((max_x + 1) * tile_width, (max_y + 1) * tile_height), "white")
    for x, y, image in tiles:
        canvas.paste(image, (x * tile_width, y * tile_height))

    # Last-row and last-column tiles can be smaller than the regular tile size.
    right = max(x * tile_width + image.width for x, _, image in tiles)
    bottom = max(y * tile_height + image.height for _, y, image in tiles)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.crop((0, 0, right, bottom)).save(output_path, quality=92, optimize=True)


if __name__ == "__main__":
    main()
