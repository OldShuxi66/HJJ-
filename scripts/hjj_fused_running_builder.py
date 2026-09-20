from __future__ import annotations

import argparse
from collections import deque
import json
import statistics
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter, ImageOps

from hjj_pet_builder import CELL_H, CELL_W, SHEET_H, SHEET_W, fit_panel


RUN_COLUMNS = 4
RUN_ROWS = 2


def is_character_palette(r: int, g: int, b: int) -> bool:
    luminance = (r + g + b) / 3
    saturation = max(r, g, b) - min(r, g, b)
    yellow = r >= g >= b and r >= 65 and g >= 35 and b <= 130
    cream = r >= 105 and g >= 80 and b >= 55 and saturation <= 120
    brown = r >= g >= b and r <= 180 and g <= 130 and b <= 100 and saturation >= 10
    skin = r >= 120 and g >= 70 and b >= 45 and r - b >= 35
    white = min(r, g, b) >= 105 and saturation <= 85
    return yellow or cream or brown or skin or white or luminance >= 175


def remove_generated_background(image: Image.Image) -> Image.Image:
    """Remove the uniform charcoal backdrop while preserving dark hair/outline."""
    image = image.convert("RGBA")
    rgb = image.convert("RGB")
    width, height = rgb.size
    pixels = rgb.load()

    foreground = bytearray(width * height)
    for y in range(height):
        for x in range(width):
            if is_character_palette(*pixels[x, y]):
                foreground[y * width + x] = 1

    visited = bytearray(width * height)
    largest: list[int] = []
    for start in range(width * height):
        if not foreground[start] or visited[start]:
            continue
        queue = deque([start])
        visited[start] = 1
        component = []
        while queue:
            current = queue.popleft()
            component.append(current)
            x = current % width
            y = current // width
            for ny in range(max(0, y - 1), min(height, y + 2)):
                for nx in range(max(0, x - 1), min(width, x + 2)):
                    neighbor = ny * width + nx
                    if foreground[neighbor] and not visited[neighbor]:
                        visited[neighbor] = 1
                        queue.append(neighbor)
        if len(component) > len(largest):
            largest = component

    main_mask = Image.new("L", (width, height), 0)
    main_pixels = main_mask.load()
    for index in largest:
        main_pixels[index % width, index // width] = 255
    # The generated hair cap sits well outside the bright face/body seed.
    # Expand enough to retain its dark pixels, while the color-distance test
    # below still rejects the uniform charcoal background.
    expanded = main_mask.filter(ImageFilter.MaxFilter(81))

    border = []
    for x in range(width):
        border.extend((pixels[x, 0], pixels[x, height - 1]))
    for y in range(1, height - 1):
        border.extend((pixels[0, y], pixels[width - 1, y]))
    bg = tuple(int(statistics.median(channel)) for channel in zip(*border))

    output = image.copy()
    out_pixels = output.load()
    expanded_pixels = expanded.load()
    for y in range(height):
        for x in range(width):
            r, g, b, _ = out_pixels[x, y]
            distance = ((r - bg[0]) ** 2 + (g - bg[1]) ** 2 + (b - bg[2]) ** 2) ** 0.5
            luminance = (r + g + b) / 3
            saturation = max(r, g, b) - min(r, g, b)
            # The deepest hair pixels are only a few RGB levels away from the
            # charcoal backdrop, so use a lower distance threshold here. The
            # expanded character mask keeps this from turning the whole panel
            # opaque.
            dark_hair_or_outline = luminance < 105 and saturation >= 2 and distance >= 4
            keep = expanded_pixels[x, y] and (is_character_palette(r, g, b) or dark_hair_or_outline)
            out_pixels[x, y] = (r, g, b, 255 if keep else 0)
    return output


def extract_running_frames(reference_path: Path) -> list[Image.Image]:
    reference = Image.open(reference_path).convert("RGB")
    if reference.width % RUN_COLUMNS or reference.height % RUN_ROWS:
        raise ValueError(f"Running reference is not a {RUN_COLUMNS}x{RUN_ROWS} grid: {reference.size}")
    panel_w = reference.width // RUN_COLUMNS
    panel_h = reference.height // RUN_ROWS
    frames = []
    for row in range(RUN_ROWS):
        for column in range(RUN_COLUMNS):
            panel = reference.crop(
                (column * panel_w, row * panel_h, (column + 1) * panel_w, (row + 1) * panel_h)
            )
            frames.append(fit_panel(remove_generated_background(panel)))
    return frames


def make_preview(sheet: Image.Image, output_path: Path) -> None:
    frames = []
    for frame_index in range(8):
        canvas = Image.new("RGBA", (CELL_W * 2, CELL_H), (255, 255, 255, 255))
        right = sheet.crop((frame_index * CELL_W, CELL_H, (frame_index + 1) * CELL_W, CELL_H * 2))
        left = sheet.crop((frame_index * CELL_W, CELL_H * 2, (frame_index + 1) * CELL_W, CELL_H * 3))
        canvas.alpha_composite(right, (0, 0))
        canvas.alpha_composite(left, (CELL_W, 0))
        frames.append(canvas.convert("RGB"))
    frames[0].save(
        output_path,
        "GIF",
        save_all=True,
        append_images=frames[1:],
        duration=[140] * len(frames),
        loop=0,
        disposal=2,
        optimize=False,
    )


def build(base_sheet_path: Path, running_reference_path: Path, output_dir: Path) -> None:
    sheet = Image.open(base_sheet_path).convert("RGBA")
    if sheet.size != (SHEET_W, SHEET_H):
        raise ValueError(f"Unexpected base sheet size: {sheet.size}")

    right_frames = extract_running_frames(running_reference_path)
    left_frames = [ImageOps.mirror(frame) for frame in right_frames]
    for frame_index in range(8):
        sheet.paste(right_frames[frame_index], (frame_index * CELL_W, CELL_H))
        sheet.paste(left_frames[frame_index], (frame_index * CELL_W, CELL_H * 2))

    output_dir.mkdir(parents=True, exist_ok=True)
    sheet_path = output_dir / "spritesheet.webp"
    manifest_path = output_dir / "pet.json"
    preview_path = output_dir / "hjj-fused-running-preview.gif"
    white_path = output_dir / "hjj-fused-sheet-white.png"
    sheet.save(sheet_path, "WEBP", lossless=True, method=6)
    manifest_path.write_text(
        json.dumps(
            {
                "id": "hjj",
                "displayName": "HJJ",
                "description": "HJJ, an overnight programmer with Nai-wa proportions, keyboard work, and a belly-laugh hover reaction.",
                "spriteVersionNumber": 2,
                "spritesheetPath": "spritesheet.webp",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    make_preview(sheet, preview_path)
    white = Image.new("RGBA", sheet.size, (255, 255, 255, 255))
    white.alpha_composite(sheet)
    white.convert("RGB").save(white_path, "PNG", optimize=True)
    print(sheet_path)
    print(manifest_path)
    print(preview_path)
    print(white_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-sheet", type=Path, required=True)
    parser.add_argument("--running-reference", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    build(args.base_sheet, args.running_reference, args.output_dir)


if __name__ == "__main__":
    main()
