import argparse
from pathlib import Path

import numpy as np
from PIL import Image
from tqdm import tqdm

from medical_image_io import DEFAULT_CT_SOURCES, DEFAULT_SEGMENTATION_SOURCES, load_image_stack


def output_name(slice_name, index):
    stem = Path(slice_name).stem
    if not stem:
        stem = f"slice_{index:03d}"
    return f"{stem}.png"


def save_image_if_changed(image, output_file):
    output_file = Path(output_file)
    if output_file.is_file():
        existing = Image.open(output_file).convert("RGB")
        if existing.size == image.size and np.array_equal(np.asarray(existing), np.asarray(image.convert("RGB"))):
            return False

    image.save(output_file)
    return True


def pair_stacks(ct_stack, segmentation_stack):
    if len(ct_stack.images) == len(segmentation_stack.images):
        return list(zip(ct_stack.images, segmentation_stack.images, ct_stack.names))

    segmentation_by_name = dict(zip(segmentation_stack.names, segmentation_stack.images))
    matched_pairs = []
    for ct_image, ct_name in zip(ct_stack.images, ct_stack.names):
        segmentation_image = segmentation_by_name.get(ct_name)
        if segmentation_image is not None:
            matched_pairs.append((ct_image, segmentation_image, ct_name))

    if matched_pairs:
        return matched_pairs

    raise ValueError(
        "CT and segmentation slice counts do not match: "
        f"CT={len(ct_stack.images)} from {ct_stack.source}, "
        f"segmentation={len(segmentation_stack.images)} from {segmentation_stack.source}"
    )


def overlay_images(
    ct_source=None,
    segmentation_source=None,
    output_folder="merged",
    threshold=240,
    ct_type="auto",
    segmentation_type="auto",
    ct_axis=2,
    segmentation_axis=2,
):
    output_path = Path(output_folder).expanduser()
    output_path.mkdir(parents=True, exist_ok=True)

    ct_stack = load_image_stack(
        ct_source,
        source_type=ct_type,
        default_sources=DEFAULT_CT_SOURCES,
        label="CT",
        axis=ct_axis,
    )
    segmentation_stack = load_image_stack(
        segmentation_source,
        source_type=segmentation_type,
        default_sources=DEFAULT_SEGMENTATION_SOURCES,
        label="segmentation",
        axis=segmentation_axis,
    )
    pairs = pair_stacks(ct_stack, segmentation_stack)

    processed_count = 0
    written_count = 0
    for index, (ct_image, segmentation_image, slice_name) in enumerate(tqdm(pairs, desc="Merging slices")):
        ct_image = ct_image.convert("RGB")
        segmentation_image = segmentation_image.convert("L")
        if ct_image.size != segmentation_image.size:
            raise ValueError(
                f"Image size mismatch for {slice_name}: "
                f"CT={ct_image.size}, segmentation={segmentation_image.size}"
            )

        ct_array = np.asarray(ct_image, dtype=np.uint8)
        segmentation_array = np.asarray(segmentation_image, dtype=np.uint8)
        tumor_mask = segmentation_array > threshold

        merged_array = ct_array.astype(float)
        merged_array[tumor_mask] = np.rint((merged_array[tumor_mask] + np.array([255, 0, 0])) / 2)
        merged_image = Image.fromarray(merged_array.astype(np.uint8))
        output_file = output_path / output_name(slice_name, index)
        if save_image_if_changed(merged_image, output_file):
            written_count += 1
        processed_count += 1

    print(
        f"Merged {processed_count} slices into: {output_path} "
        f"({written_count} files written; unchanged files skipped; "
        f"CT: {ct_stack.source_type} {ct_stack.source}; segmentation: "
        f"{segmentation_stack.source_type} {segmentation_stack.source})"
    )


def main():
    parser = argparse.ArgumentParser(description="Overlay segmentation masks on CT slices in red.")
    parser.add_argument(
        "--ct",
        default=None,
        help="CT source: DICOM folder, NIfTI file, PNG folder, PNG file, or PNG glob. Defaults to bundled paths.",
    )
    parser.add_argument(
        "--segmentation",
        "--segmentct",
        dest="segmentation",
        default=None,
        help="Segmentation source: DICOM folder, NIfTI file, PNG folder, PNG file, or PNG glob. Defaults to bundled paths.",
    )
    parser.add_argument("--ct-type", choices=["auto", "png", "nii", "dicom"], default="auto", help="CT source type.")
    parser.add_argument(
        "--segmentation-type",
        "--segmentct-type",
        dest="segmentation_type",
        choices=["auto", "png", "nii", "dicom"],
        default="auto",
        help="Segmentation source type.",
    )
    parser.add_argument("--ct-axis", type=int, default=2, help="Slice axis for CT NIfTI input.")
    parser.add_argument(
        "--segmentation-axis",
        "--segmentct-axis",
        dest="segmentation_axis",
        type=int,
        default=2,
        help="Slice axis for segmentation NIfTI input.",
    )
    parser.add_argument("--output", default="merged", help="Output folder for merged PNG slices.")
    parser.add_argument("--threshold", type=int, default=240, help="Segmentation pixel threshold.")
    args = parser.parse_args()
    overlay_images(
        ct_source=args.ct,
        segmentation_source=args.segmentation,
        output_folder=args.output,
        threshold=args.threshold,
        ct_type=args.ct_type,
        segmentation_type=args.segmentation_type,
        ct_axis=args.ct_axis,
        segmentation_axis=args.segmentation_axis,
    )


if __name__ == "__main__":
    main()
