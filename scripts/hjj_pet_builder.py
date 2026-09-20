from __future__ import annotations

import argparse
from collections import deque
import json
import statistics
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


CELL_W = 192
CELL_H = 208
SHEET_W = CELL_W * 8
SHEET_H = CELL_H * 11
PANEL_SIZE = 408
PANEL_ORIGINS = (7, 423, 839)


def remove_dark_background(image: Image.Image, hair_mask: Image.Image) -> Image.Image:
    """Keep the main character and nearby props, removing panel artifacts."""
    image = image.convert("RGBA")
    rgb = image.convert("RGB")
    width, height = rgb.size

    border = []
    for x in range(width):
        border.append(rgb.getpixel((x, 0)))
        border.append(rgb.getpixel((x, height - 1)))
    for y in range(1, height - 1):
        border.append(rgb.getpixel((0, y)))
        border.append(rgb.getpixel((width - 1, y)))
    usable_border = [pixel for pixel in border if 10 <= sum(pixel) / 3 <= 45]
    if not usable_border:
        usable_border = border
    bg = tuple(int(statistics.median(channel)) for channel in zip(*usable_border))

    def is_character_palette(r: int, g: int, b: int) -> bool:
        luminance = (r + g + b) / 3
        saturation = max(r, g, b) - min(r, g, b)
        yellow = r >= g >= b and r >= 65 and g >= 35 and b <= 115
        cream = r >= 105 and g >= 80 and b >= 55 and saturation <= 110
        brown = r >= g >= b and r <= 180 and g <= 125 and b <= 90 and saturation >= 10
        white = min(r, g, b) >= 105 and saturation <= 75
        return yellow or cream or brown or white or luminance >= 175

    # Bright/colorful pixels form a reliable foreground seed. The generated
    # storyboard has long decorative dark lines in some panels; selecting the
    # largest connected seed component keeps those lines out of the pet.
    foreground = bytearray(width * height)
    for y in range(height):
        for x in range(width):
            r, g, b = rgb.getpixel((x, y))
            if is_character_palette(r, g, b):
                foreground[y * width + x] = 1

    visited = bytearray(width * height)
    largest_component: list[int] = []
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
        if len(component) > len(largest_component):
            largest_component = component

    main_mask = Image.new("L", (width, height), 0)
    mask_pixels = main_mask.load()
    for index in largest_component:
        mask_pixels[index % width, index // width] = 255
    # Include only a tight neighborhood around the main component. This keeps
    # dark hair and outlines but cuts off the generated panel's long dark lines.
    expanded = main_mask.filter(ImageFilter.MaxFilter(17))
    expanded_pixels = expanded.load()
    hair_pixels = hair_mask.load()
    output_pixels = image.load()
    for y in range(height):
        for x in range(width):
            r, g, b, _ = output_pixels[x, y]
            # The source artwork's black hair is close to the charcoal panel
            # background, so preserve/fill it explicitly before chroma cleanup.
            if hair_pixels[x, y]:
                if output_pixels[x, y][3] == 0:
                    output_pixels[x, y] = (30, 25, 22, 255)
                continue
            distance = ((r - bg[0]) ** 2 + (g - bg[1]) ** 2 + (b - bg[2]) ** 2) ** 0.5
            luminance = (r + g + b) / 3
            saturation = max(r, g, b) - min(r, g, b)
            dark_hair_or_outline = luminance < 95 and saturation >= 3 and distance >= 9
            is_character_color = is_character_palette(r, g, b) or dark_hair_or_outline
            if not expanded_pixels[x, y] or not is_character_color:
                output_pixels[x, y] = (r, g, b, 0)
    return image


def hair_mask_for_panel(panel_index: int) -> Image.Image:
    mask = Image.new("L", (PANEL_SIZE, PANEL_SIZE), 0)
    draw = ImageDraw.Draw(mask)
    front = [
        (115, 180), (112, 145), (122, 108), (145, 78), (180, 60),
        (220, 60), (260, 75), (290, 100), (305, 135), (300, 165),
        (285, 185), (265, 170), (250, 150), (225, 158), (205, 170),
        (185, 155), (165, 172), (145, 190),
    ]
    side_left = [
        (120, 180), (118, 145), (125, 110), (145, 80), (180, 62),
        (225, 65), (265, 88), (290, 120), (292, 150), (280, 175),
        (255, 175), (230, 145), (200, 160), (170, 175), (145, 190),
    ]
    sleep = [
        (45, 270), (50, 225), (70, 195), (105, 180), (145, 185),
        (175, 210), (175, 245), (155, 275), (125, 300), (85, 300),
        (55, 290),
    ]
    if panel_index in (1, 2):
        points = side_left
        if panel_index == 2:
            points = [(PANEL_SIZE - x, y) for x, y in points]
    elif panel_index == 6:
        points = sleep
    elif panel_index == 8:
        # The mouse-look panel places HJJ left of center to leave room for
        # the cursor, so its hair cap must move with the character.
        points = [(x - 55, y) for x, y in front]
    else:
        points = front
    draw.polygon(points, fill=255)
    return mask


def make_panel_images(storyboard_path: Path) -> list[Image.Image]:
    storyboard = Image.open(storyboard_path).convert("RGB")
    panels = []
    for panel_index, (y, x) in enumerate((
        (y, x) for y in PANEL_ORIGINS for x in PANEL_ORIGINS
    )):
            panel = storyboard.crop((x, y, x + PANEL_SIZE, y + PANEL_SIZE))
            panels.append(remove_dark_background(panel, hair_mask_for_panel(panel_index)))
    return panels


def fit_panel(panel: Image.Image, max_w: int = 178, max_h: int = 194) -> Image.Image:
    alpha = panel.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        return Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0))
    panel = panel.crop(bbox)
    scale = min(max_w / panel.width, max_h / panel.height)
    size = (max(1, round(panel.width * scale)), max(1, round(panel.height * scale)))
    panel = panel.resize(size, Image.Resampling.NEAREST)
    cell = Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0))
    cell.alpha_composite(panel, ((CELL_W - size[0]) // 2, (CELL_H - size[1]) // 2))
    return cell


def animate_cell(base: Image.Image, frame_index: int, row_index: int) -> Image.Image:
    """Add restrained bob/shift so repeated concept poses still read as animation."""
    scale_cycle = (1.00, 1.015, 1.00, 0.985, 1.00, 1.015, 1.00, 0.985)
    bob_cycle = (0, -2, 0, 2, 0, -2, 0, 2)
    x_cycle = (0, 1, 0, -1, 0, 1, 0, -1)
    scale = scale_cycle[frame_index % len(scale_cycle)]
    scaled = base.resize((round(CELL_W * scale), round(CELL_H * scale)), Image.Resampling.NEAREST)
    cell = Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0))
    left = (CELL_W - scaled.width) // 2 + x_cycle[frame_index % len(x_cycle)]
    top = (CELL_H - scaled.height) // 2 + bob_cycle[frame_index % len(bob_cycle)]
    cell.alpha_composite(scaled, (left, top))
    return cell


def repair_running_rows(sheet: Image.Image, nai_wa: Image.Image) -> None:
    """Give HJJ the real alternating Nai-wa running cadence.

    The approved HJJ side-view artwork is used as the head source, while the
    original Nai-wa side rows supply the moving arms, belly, feet, and tail.
    This keeps HJJ's identity and the already-correct Codex left/right row
    mapping, but prevents dragging from reading as a static slide.
    """
    head_height = 104
    head_sources = {
        row_index: sheet.crop((0, row_index * CELL_H, CELL_W, row_index * CELL_H + head_height)).copy()
        for row_index in (1, 2)
    }
    for row_index in (1, 2):
        for frame_index in range(8):
            # Nai-wa row 1 faces right and row 2 faces left. HJJ uses the
            # same v2 directional ordering after the storyboard swap above.
            body = nai_wa.crop(
                (
                    frame_index * CELL_W,
                    row_index * CELL_H,
                    (frame_index + 1) * CELL_W,
                    (row_index + 1) * CELL_H,
                )
            ).convert("RGBA")
            body.alpha_composite(head_sources[row_index], (0, 0))
            sheet.paste(body, (frame_index * CELL_W, row_index * CELL_H))


def build_sheet(storyboard_path: Path, nai_wa_sheet_path: Path, output_dir: Path) -> None:
    nai_wa = Image.open(nai_wa_sheet_path)
    if nai_wa.size != (SHEET_W, SHEET_H):
        raise ValueError(f"Unexpected Nai-wa sheet size: {nai_wa.size}")

    panels = make_panel_images(storyboard_path)
    # Contact-sheet order: idle, walk-left, walk-right, work, laugh, think,
    # sleep, error, mouse-look. Rows mirror the major behaviors in Nai-wa's v2 sheet.
    # Codex's horizontal drag mapping expects the opposite order from the
    # storyboard's visual left/right order, so swap these two walking rows.
    action_rows = (0, 2, 1, 0, 4, 6, 8, 3, 5, 7, 8)
    base_cells = [fit_panel(panel) for panel in panels]

    sheet = Image.new("RGBA", (SHEET_W, SHEET_H), (0, 0, 0, 0))
    representative_frames = []
    for row_index, action_index in enumerate(action_rows):
        row_frames = []
        for frame_index in range(8):
            cell = animate_cell(base_cells[action_index], frame_index, row_index)
            sheet.alpha_composite(cell, (frame_index * CELL_W, row_index * CELL_H))
            row_frames.append(cell)
        representative_frames.append(row_frames[0])

    repair_running_rows(sheet, nai_wa)
    representative_frames[1] = sheet.crop((0, CELL_H, CELL_W, CELL_H * 2))
    representative_frames[2] = sheet.crop((0, CELL_H * 2, CELL_W, CELL_H * 3))

    output_dir.mkdir(parents=True, exist_ok=True)
    sheet_path = output_dir / "spritesheet.webp"
    manifest_path = output_dir / "pet.json"
    preview_path = output_dir / "hjj-final-preview.gif"
    running_preview_path = output_dir / "hjj-running-preview.gif"
    white_sheet_path = output_dir / "hjj-sheet-white.png"
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
    representative_frames[0].save(
        preview_path,
        "GIF",
        save_all=True,
        append_images=representative_frames[1:],
        duration=[650] * len(representative_frames),
        loop=0,
        disposal=2,
        optimize=False,
    )
    running_frames = []
    for frame_index in range(8):
        canvas = Image.new("RGBA", (CELL_W * 2, CELL_H), (255, 255, 255, 255))
        right = sheet.crop(
            (frame_index * CELL_W, CELL_H, (frame_index + 1) * CELL_W, CELL_H * 2)
        )
        left = sheet.crop(
            (frame_index * CELL_W, CELL_H * 2, (frame_index + 1) * CELL_W, CELL_H * 3)
        )
        canvas.alpha_composite(right, (0, 0))
        canvas.alpha_composite(left, (CELL_W, 0))
        running_frames.append(canvas.convert("RGB"))
    running_frames[0].save(
        running_preview_path,
        "GIF",
        save_all=True,
        append_images=running_frames[1:],
        duration=[140] * len(running_frames),
        loop=0,
        disposal=2,
        optimize=False,
    )
    white_sheet = Image.new("RGBA", sheet.size, (255, 255, 255, 255))
    white_sheet.alpha_composite(sheet)
    white_sheet.convert("RGB").save(white_sheet_path, "PNG", optimize=True)
    print(sheet_path)
    print(manifest_path)
    print(preview_path)
    print(running_preview_path)
    print(white_sheet_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--storyboard", type=Path, required=True)
    parser.add_argument("--nai-wa-sheet", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    build_sheet(args.storyboard, args.nai_wa_sheet, args.output_dir)


if __name__ == "__main__":
    main()
