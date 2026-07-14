import argparse
from pathlib import Path

import nibabel as nib
import numpy as np
from PIL import Image


def normalize_to_uint8(slice_data):
    finite_slice = np.nan_to_num(slice_data, nan=0.0, posinf=0.0, neginf=0.0)
    min_value = float(np.min(finite_slice))
    max_value = float(np.max(finite_slice))
    if max_value <= min_value:
        return np.zeros(finite_slice.shape, dtype=np.uint8)
    normalized = (finite_slice - min_value) / (max_value - min_value) * 255
    return normalized.astype(np.uint8)


def split_nii_to_png(nii_file, output_dir, axis=2):
    nii_path = Path(nii_file).expanduser()
    output_path = Path(output_dir).expanduser()
    if not nii_path.is_file():
        raise FileNotFoundError(f"NIfTI file not found: {nii_path}")

    data = nib.load(str(nii_path)).get_fdata()
    if axis < 0 or axis >= data.ndim:
        raise ValueError(f"Axis {axis} is invalid for data with {data.ndim} dimensions.")

    output_path.mkdir(parents=True, exist_ok=True)
    moved = np.moveaxis(data, axis, 2)
    for i in range(moved.shape[2]):
        image = Image.fromarray(normalize_to_uint8(moved[:, :, i]))
        image.save(output_path / f"slice_{i:03d}.png")

    print(f"Saved {moved.shape[2]} slices to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Split CT.nii into PNG slices.")
    parser.add_argument("nii_file", nargs="?", default="CT.nii", help="Input NIfTI CT file.")
    parser.add_argument("--output", default="CT", help="Output folder for PNG slices.")
    parser.add_argument("--axis", type=int, default=2, help="Slice axis. Default: 2.")
    args = parser.parse_args()
    split_nii_to_png(args.nii_file, args.output, args.axis)


if __name__ == "__main__":
    main()
