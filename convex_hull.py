import argparse
from pathlib import Path

import numpy as np
from scipy.spatial import ConvexHull
from stl import mesh


def generate_convex_hull(input_stl, output_stl):
    input_path = Path(input_stl).expanduser()
    output_path = Path(output_stl).expanduser()

    if not input_path.is_file():
        raise FileNotFoundError(f"Input STL file not found: {input_path}")

    stl_mesh = mesh.Mesh.from_file(str(input_path))
    points = np.asarray(stl_mesh.vectors, dtype=float).reshape(-1, 3)
    points = np.unique(points, axis=0)
    if len(points) < 4:
        raise ValueError("At least four unique 3D points are required to build a convex hull.")

    hull = ConvexHull(points)
    hull_mesh = mesh.Mesh(np.zeros(hull.simplices.shape[0], dtype=mesh.Mesh.dtype))

    for i, simplex in enumerate(hull.simplices):
        for j in range(3):
            hull_mesh.vectors[i][j] = points[simplex[j]]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    hull_mesh.save(str(output_path))
    print(f"Convex hull saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate a convex-hull STL from a tumor STL model.")
    parser.add_argument("input_stl", nargs="?", default="tumor.stl", help="Input tumor STL file.")
    parser.add_argument("output_stl", nargs="?", default="tumor_hull.stl", help="Output hull STL file.")
    args = parser.parse_args()
    generate_convex_hull(args.input_stl, args.output_stl)


if __name__ == "__main__":
    main()
