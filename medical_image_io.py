import glob
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}

DEFAULT_CT_SOURCES = [
    Path("CT"),
    Path("CT.nii"),
    Path("CT.nii.gz"),
    Path("DICOM/CT"),
    Path("CT_DICOM"),
]

DEFAULT_SEGMENTATION_SOURCES = [
    Path("SegmentationCT"),
    Path("SegmentCT"),
    Path("SegmentationCT.nii"),
    Path("SegmentCT.nii"),
    Path("SegmentationCT.nii.gz"),
    Path("SegmentCT.nii.gz"),
    Path("DICOM/SegmentationCT"),
    Path("DICOM/SegmentCT"),
    Path("SegmentationCT_DICOM"),
    Path("SegmentCT_DICOM"),
]

DEFAULT_CT_EXPORT_SOURCES = [
    Path("CT.nii"),
    Path("CT.nii.gz"),
    Path("DICOM/CT"),
    Path("CT_DICOM"),
    Path("CT"),
]

DEFAULT_SEGMENTATION_EXPORT_SOURCES = [
    Path("SegmentationCT.nii"),
    Path("SegmentCT.nii"),
    Path("SegmentationCT.nii.gz"),
    Path("SegmentCT.nii.gz"),
    Path("DICOM/SegmentationCT"),
    Path("DICOM/SegmentCT"),
    Path("SegmentationCT_DICOM"),
    Path("SegmentCT_DICOM"),
    Path("SegmentationCT"),
    Path("SegmentCT"),
]


@dataclass
class ImageStack:
    images: list
    names: list
    source: str
    source_type: str


def has_glob_pattern(value):
    return any(char in str(value) for char in "*?[]")


def source_exists(source):
    if has_glob_pattern(source):
        return bool(glob.glob(str(source)))
    return Path(source).expanduser().exists()


def resolve_source(source, default_sources, label):
    if source:
        if not source_exists(source):
            raise FileNotFoundError(f"{label} source not found: {source}")
        return source

    for candidate in default_sources:
        if source_exists(candidate):
            return str(candidate)

    defaults = ", ".join(str(candidate) for candidate in default_sources)
    raise FileNotFoundError(f"No {label} source specified and no default source was found. Tried: {defaults}")


def detect_source_type(source, source_type="auto"):
    if source_type != "auto":
        return source_type

    source_text = str(source)
    path = Path(source_text).expanduser()
    lower_name = path.name.lower()

    if has_glob_pattern(source_text):
        return "png"
    if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
        return "png"
    if lower_name.endswith(".nii") or lower_name.endswith(".nii.gz"):
        return "nii"
    if path.is_dir():
        if list_image_files(path):
            return "png"
        return "dicom"

    raise ValueError(f"Cannot infer source type for: {source}")


def list_image_files(source):
    path = Path(source).expanduser()
    if path.is_dir():
        files = [item for item in path.iterdir() if item.is_file() and item.suffix.lower() in IMAGE_EXTENSIONS]
        return sorted(files)
    if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
        return [path]
    return []


def expand_png_sequence(source):
    source_text = str(source)
    if has_glob_pattern(source_text):
        files = [Path(item) for item in glob.glob(source_text)]
        files = [item for item in files if item.is_file() and item.suffix.lower() in IMAGE_EXTENSIONS]
        return sorted(files)
    return list_image_files(source)


def normalize_to_uint8(slice_data):
    finite_slice = np.nan_to_num(slice_data, nan=0.0, posinf=0.0, neginf=0.0)
    min_value = float(np.min(finite_slice))
    max_value = float(np.max(finite_slice))
    if max_value <= min_value:
        return np.zeros(finite_slice.shape, dtype=np.uint8)
    normalized = (finite_slice - min_value) / (max_value - min_value) * 255
    return np.rint(normalized).astype(np.uint8)


def volume_to_images(volume, axis=2):
    volume = np.asarray(volume)
    volume = np.squeeze(volume)

    if volume.ndim == 2:
        moved = volume[:, :, np.newaxis]
    elif volume.ndim == 3:
        if axis < 0 or axis >= volume.ndim:
            raise ValueError(f"Axis {axis} is invalid for data with {volume.ndim} dimensions.")
        moved = np.moveaxis(volume, axis, 2)
    else:
        raise ValueError(f"Expected a 2D or 3D image volume, got shape {volume.shape}.")

    images = []
    names = []
    for index in range(moved.shape[2]):
        images.append(Image.fromarray(normalize_to_uint8(moved[:, :, index])))
        names.append(f"slice_{index:03d}.png")
    return images, names


def load_png_stack(source):
    files = expand_png_sequence(source)
    if not files:
        raise FileNotFoundError(f"No PNG sequence files found for: {source}")

    images = [Image.open(file_path).convert("L") for file_path in files]
    names = [file_path.name for file_path in files]
    return images, names


def load_nii_stack(source, axis=2):
    try:
        import nibabel as nib
    except ImportError as exc:
        raise ImportError("NIfTI input requires nibabel. Install dependencies with: pip install -r requirements.txt") from exc

    path = Path(source).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"NIfTI file not found: {path}")

    data = nib.load(str(path)).get_fdata()
    return volume_to_images(data, axis)


def dicom_sort_key(dataset, file_path):
    image_position = getattr(dataset, "ImagePositionPatient", None)
    if image_position is not None and len(image_position) >= 3:
        return (0, float(image_position[2]), str(file_path))

    slice_location = getattr(dataset, "SliceLocation", None)
    if slice_location is not None:
        return (1, float(slice_location), str(file_path))

    instance_number = getattr(dataset, "InstanceNumber", None)
    if instance_number is not None:
        return (2, int(instance_number), str(file_path))

    return (3, str(file_path))


def load_dicom_stack(source):
    try:
        import pydicom
    except ImportError as exc:
        raise ImportError("DICOM input requires pydicom. Install dependencies with: pip install -r requirements.txt") from exc

    dicom_dir = Path(source).expanduser()
    if not dicom_dir.is_dir():
        raise FileNotFoundError(f"DICOM source must be a folder: {dicom_dir}")

    records = []
    for file_path in sorted(item for item in dicom_dir.rglob("*") if item.is_file()):
        try:
            dataset = pydicom.dcmread(str(file_path), force=True)
            if "PixelData" not in dataset:
                continue
            pixel_array = dataset.pixel_array.astype(float)
        except Exception:
            continue

        slope = float(getattr(dataset, "RescaleSlope", 1.0))
        intercept = float(getattr(dataset, "RescaleIntercept", 0.0))
        pixel_array = pixel_array * slope + intercept

        if getattr(dataset, "PhotometricInterpretation", "") == "MONOCHROME1":
            pixel_array = np.max(pixel_array) - pixel_array

        key = dicom_sort_key(dataset, file_path)
        if pixel_array.ndim == 2:
            records.append((key, pixel_array))
        elif pixel_array.ndim == 3:
            for frame_index, frame in enumerate(pixel_array):
                records.append((key + (frame_index,), frame))

    if not records:
        raise FileNotFoundError(f"No readable DICOM pixel data found in: {dicom_dir}")

    records.sort(key=lambda item: item[0])
    shapes = {record[1].shape for record in records}
    if len(shapes) != 1:
        raise ValueError(f"DICOM slices have inconsistent shapes: {sorted(shapes)}")

    volume = np.stack([record[1] for record in records], axis=2)
    return volume_to_images(volume, axis=2)


def load_image_stack(source=None, source_type="auto", default_sources=None, label="image", axis=2):
    resolved_source = resolve_source(source, default_sources or [], label)
    detected_type = detect_source_type(resolved_source, source_type)

    if detected_type == "png":
        images, names = load_png_stack(resolved_source)
    elif detected_type == "nii":
        images, names = load_nii_stack(resolved_source, axis)
    elif detected_type == "dicom":
        images, names = load_dicom_stack(resolved_source)
    else:
        raise ValueError(f"Unsupported source type: {detected_type}")

    return ImageStack(images=images, names=names, source=str(resolved_source), source_type=detected_type)


def save_stack_as_png(stack, output_dir):
    output_path = Path(output_dir).expanduser()
    output_path.mkdir(parents=True, exist_ok=True)

    for index, image in enumerate(stack.images):
        stem = Path(stack.names[index]).stem or f"slice_{index:03d}"
        image.save(output_path / f"{stem}.png")

    return len(stack.images)
