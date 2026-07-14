import argparse
from pathlib import Path

import numpy as np
from stl import mesh


def parse_vector(value):
    parts = [part.strip() for part in value.split(",")]
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("Expected a vector in the form x,y,z.")
    try:
        return np.array([float(part) for part in parts], dtype=float)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Vector values must be numbers.") from exc


def find_tangent_planes(input_stl, normal_vector):
    input_path = Path(input_stl).expanduser()
    if not input_path.is_file():
        raise FileNotFoundError(f"STL file not found: {input_path}")

    normal = np.asarray(normal_vector, dtype=float)
    normal_norm = np.linalg.norm(normal)
    if normal_norm == 0:
        raise ValueError("normal_vector must not be the zero vector.")
    normal = normal / normal_norm

    stl_mesh = mesh.Mesh.from_file(str(input_path))
    points = np.asarray(stl_mesh.vectors, dtype=float).reshape(-1, 3)
    if points.size == 0:
        raise ValueError(f"STL file has no vertices: {input_path}")

    distances = np.dot(points, normal)
    min_distance_index = int(np.argmin(distances))
    max_distance_index = int(np.argmax(distances))

    d1 = -float(np.dot(normal, points[min_distance_index]))
    d2 = -float(np.dot(normal, points[max_distance_index]))

    return (normal, d1, points[min_distance_index]), (normal, d2, points[max_distance_index])


def main():
    parser = argparse.ArgumentParser(
        description="Find the two tangent planes of an STL convex hull for a support vector."
    )
    parser.add_argument("input_stl", nargs="?", default="tumor_hull.stl", help="Input convex-hull STL file.")
    parser.add_argument(
        "--normal",
        type=parse_vector,
        default=np.array([0.1, -0.5, 1.0], dtype=float),
        help="Support vector as x,y,z. Default: 0.1,-0.5,1",
    )
    args = parser.parse_args()

    plane1, plane2 = find_tangent_planes(args.input_stl, args.normal)
    print("Negative tangent plane:", plane1)
    print("Positive tangent plane:", plane2)


if __name__ == "__main__":
    main()
