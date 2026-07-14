import argparse
from pathlib import Path

from medical_image_io import (
    DEFAULT_SEGMENTATION_EXPORT_SOURCES,
    has_glob_pattern,
    load_image_stack,
    save_stack_as_png,
)


def source_is_output_folder(stack, output_dir):
    if stack.source_type != "png" or has_glob_pattern(stack.source):
        return False
    source_path = Path(stack.source).expanduser()
    output_path = Path(output_dir).expanduser()
    return source_path.is_dir() and source_path.resolve() == output_path.resolve()


def split_nii_to_png(source=None, output_dir="SegmentationCT", axis=2, source_type="auto"):
    stack = load_image_stack(
        source,
        source_type=source_type,
        default_sources=DEFAULT_SEGMENTATION_EXPORT_SOURCES,
        label="segmentation",
        axis=axis,
    )
    if source_is_output_folder(stack, output_dir):
        print(f"Source already points to output PNG folder: {output_dir}. No files were rewritten.")
        return

    saved_count = save_stack_as_png(stack, output_dir)
    print(f"Saved {saved_count} slices to: {output_dir} (source: {stack.source_type} {stack.source})")


def main():
    parser = argparse.ArgumentParser(description="Export a segmentation source to PNG slices.")
    parser.add_argument(
        "source",
        nargs="?",
        default=None,
        help="Segmentation source: DICOM folder, NIfTI file, PNG folder, PNG file, or PNG glob.",
    )
    parser.add_argument("--source-type", choices=["auto", "png", "nii", "dicom"], default="auto", help="Input type.")
    parser.add_argument("--output", default="SegmentationCT", help="Output folder for PNG slices.")
    parser.add_argument("--axis", type=int, default=2, help="Slice axis for NIfTI input. Default: 2.")
    args = parser.parse_args()
    split_nii_to_png(args.source, args.output, args.axis, args.source_type)


if __name__ == "__main__":
    main()
