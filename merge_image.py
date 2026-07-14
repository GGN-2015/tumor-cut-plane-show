import argparse
from pathlib import Path

import numpy as np
from PIL import Image
from tqdm import tqdm


def overlay_images(ct_folder, segmentation_folder, output_folder, threshold=240):
    ct_path = Path(ct_folder).expanduser()
    segmentation_path = Path(segmentation_folder).expanduser()
    output_path = Path(output_folder).expanduser()

    if not ct_path.is_dir():
        raise FileNotFoundError(f"CT folder not found: {ct_path}")
    if not segmentation_path.is_dir():
        raise FileNotFoundError(f"Segmentation folder not found: {segmentation_path}")

    output_path.mkdir(parents=True, exist_ok=True)
    ct_files = sorted(ct_path.glob("*.png"))
    if not ct_files:
        raise FileNotFoundError(f"No PNG files found in CT folder: {ct_path}")

    saved_count = 0
    skipped_count = 0
    for ct_file in tqdm(ct_files, desc="Merging slices"):
        segmentation_file = segmentation_path / ct_file.name
        if not segmentation_file.is_file():
            skipped_count += 1
            continue

        ct_image = Image.open(ct_file).convert("RGB")
        segmentation_image = Image.open(segmentation_file).convert("RGB")
        if ct_image.size != segmentation_image.size:
            raise ValueError(
                f"Image size mismatch for {ct_file.name}: "
                f"CT={ct_image.size}, segmentation={segmentation_image.size}"
            )

        ct_array = np.asarray(ct_image, dtype=np.uint8)
        segmentation_array = np.asarray(segmentation_image, dtype=np.uint8)
        tumor_mask = np.all(segmentation_array > threshold, axis=-1)

        merged_array = ct_array.astype(float)
        merged_array[tumor_mask] = np.rint((merged_array[tumor_mask] + np.array([255, 0, 0])) / 2)
        Image.fromarray(merged_array.astype(np.uint8)).save(output_path / ct_file.name)
        saved_count += 1

    print(f"Merged {saved_count} slices into: {output_path}")
    if skipped_count:
        print(f"Skipped {skipped_count} CT slices because matching segmentation files were missing.")


def main():
    parser = argparse.ArgumentParser(description="Overlay segmentation masks on CT slices in red.")
    parser.add_argument("--ct", default="CT", help="Folder containing CT PNG slices.")
    parser.add_argument("--segmentation", default="SegmentationCT", help="Folder containing segmentation PNG slices.")
    parser.add_argument("--output", default="merged", help="Output folder for merged PNG slices.")
    parser.add_argument("--threshold", type=int, default=240, help="Segmentation pixel threshold.")
    args = parser.parse_args()
    overlay_images(args.ct, args.segmentation, args.output, args.threshold)


if __name__ == "__main__":
    main()
