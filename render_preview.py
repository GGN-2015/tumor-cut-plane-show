import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


def find_best_slice(segmentation_folder):
    segmentation_path = Path(segmentation_folder)
    best_name = None
    best_score = -1

    for image_path in sorted(segmentation_path.glob("*.png")):
        mask = np.asarray(Image.open(image_path).convert("L"))
        score = int((mask > 240).sum())
        if score > best_score:
            best_score = score
            best_name = image_path.name

    if best_name is None:
        raise FileNotFoundError(f"No PNG files found in segmentation folder: {segmentation_path}")
    return best_name


def resize_to_fit(image, size):
    fitted = image.copy()
    fitted.thumbnail(size, Image.Resampling.LANCZOS)
    background = Image.new("RGB", size, (15, 23, 42))
    x = (size[0] - fitted.width) // 2
    y = (size[1] - fitted.height) // 2
    background.paste(fitted, (x, y))
    return background


def mask_to_preview(mask_image):
    mask = np.asarray(mask_image.convert("L"))
    preview = np.zeros((mask.shape[0], mask.shape[1], 3), dtype=np.uint8)
    preview[:, :, :] = [20, 28, 44]
    preview[mask > 240] = [239, 68, 68]
    return Image.fromarray(preview)


def line_box_points(normal, offset, width, height):
    nx, ny = normal
    candidates = []

    if abs(ny) > 1e-9:
        for x in (0.0, float(width - 1)):
            y = (offset - nx * x) / ny
            if 0 <= y <= height - 1:
                candidates.append((x, y))

    if abs(nx) > 1e-9:
        for y in (0.0, float(height - 1)):
            x = (offset - ny * y) / nx
            if 0 <= x <= width - 1:
                candidates.append((x, y))

    unique = []
    for point in candidates:
        if not any(np.linalg.norm(np.array(point) - np.array(existing)) < 1e-6 for existing in unique):
            unique.append(point)

    if len(unique) < 2:
        raise ValueError("Could not intersect cut-plane guide with the image bounds.")

    direction = np.array([-ny, nx])
    unique.sort(key=lambda point: float(np.dot(point, direction)))
    return unique[0], unique[-1]


def tangent_plane_band(mask, normal, clearance=4.0, band_width=18.0):
    y_coords, x_coords = np.nonzero(mask)
    if len(x_coords) == 0:
        raise ValueError("Cannot place a tangent plane without a tumor mask.")

    points = np.column_stack([x_coords, y_coords]).astype(float)
    support = float(np.max(points @ normal))
    inner_offset = support + clearance
    outer_offset = inner_offset + band_width

    height, width = mask.shape
    inner_points = line_box_points(normal, inner_offset, width, height)
    outer_points = line_box_points(normal, outer_offset, width, height)
    polygon = [inner_points[0], inner_points[1], outer_points[1], outer_points[0]]

    yy, xx = np.mgrid[0:height, 0:width]
    signed_distance = xx * normal[0] + yy * normal[1]
    band_mask = (signed_distance >= inner_offset) & (signed_distance <= outer_offset)
    return polygon, inner_points, outer_points, band_mask


def add_cut_plane_hint(image, mask_image):
    preview = image.convert("RGBA")
    mask = np.asarray(mask_image.convert("L")) > 240
    normal = np.array([0.58, 0.82], dtype=float)
    normal = normal / np.linalg.norm(normal)
    polygon, inner_points, outer_points, band_mask = tangent_plane_band(mask, normal)

    overlay = Image.new("RGBA", preview.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")
    draw.polygon(polygon, fill=(250, 204, 21, 72), outline=(254, 240, 138, 220))
    draw.line(inner_points, fill=(254, 240, 138, 255), width=3)
    draw.line(outer_points, fill=(250, 204, 21, 110), width=1)

    if np.any(band_mask & mask):
        raise ValueError("Cut-plane preview overlaps the tumor mask.")

    return Image.alpha_composite(preview, overlay).convert("RGB")


def get_font(size, bold=False):
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def draw_panel(canvas, bounds, title, subtitle, image):
    draw = ImageDraw.Draw(canvas)
    x, y, width, height = bounds
    radius = 14
    draw.rounded_rectangle((x, y, x + width, y + height), radius=radius, fill=(15, 23, 42), outline=(71, 85, 105))
    draw.text((x + 22, y + 18), title, fill=(248, 250, 252), font=get_font(24, bold=True))
    draw.text((x + 22, y + 50), subtitle, fill=(148, 163, 184), font=get_font(15))

    image_box = (width - 44, height - 88)
    fitted = resize_to_fit(image, image_box)
    canvas.paste(fitted, (x + 22, y + 76))


def build_preview(ct_folder, segmentation_folder, merged_folder, output_file, slice_name=None):
    ct_path = Path(ct_folder)
    segmentation_path = Path(segmentation_folder)
    merged_path = Path(merged_folder)
    output_path = Path(output_file)

    selected_slice = slice_name or find_best_slice(segmentation_path)
    ct_image = Image.open(ct_path / selected_slice).convert("RGB")
    segmentation_image = Image.open(segmentation_path / selected_slice).convert("RGB")
    merged_image = Image.open(merged_path / selected_slice).convert("RGB")
    merged_with_plane = add_cut_plane_hint(merged_image, segmentation_image)

    canvas = Image.new("RGB", (1280, 720), (2, 6, 23))
    draw = ImageDraw.Draw(canvas)
    draw.text((48, 34), "Tumor Cut-Plane Rendering Preview", fill=(248, 250, 252), font=get_font(40, bold=True))
    draw.text(
        (50, 86),
        f"Generated from bundled sample slice {selected_slice}",
        fill=(148, 163, 184),
        font=get_font(18),
    )

    draw_panel(
        canvas,
        (48, 132, 584, 540),
        "CT + Tumor + Tangent Plane",
        "Yellow guide stays outside the tumor contour",
        merged_with_plane,
    )
    draw_panel(canvas, (664, 132, 260, 252), "Raw CT", "Original slice", ct_image)
    draw_panel(canvas, (972, 132, 260, 252), "Tumor Mask", "Segmentation", mask_to_preview(segmentation_image))
    draw_panel(canvas, (664, 420, 568, 252), "Merged Slice", "Tumor region overlaid in red", merged_image)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)
    print(f"Preview image saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate the README rendering preview from bundled PNG slices.")
    parser.add_argument("--ct", default="CT", help="Folder containing CT PNG slices.")
    parser.add_argument("--segmentation", default="SegmentationCT", help="Folder containing segmentation PNG slices.")
    parser.add_argument("--merged", default="merged", help="Folder containing merged PNG slices.")
    parser.add_argument("--slice", default=None, help="Slice file name to render, for example slice_009.png.")
    parser.add_argument("--output", default="docs/render-preview.png", help="Output preview image.")
    args = parser.parse_args()
    build_preview(args.ct, args.segmentation, args.merged, args.output, args.slice)


if __name__ == "__main__":
    main()
