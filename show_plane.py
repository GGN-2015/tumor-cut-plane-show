import argparse
from pathlib import Path

import numpy as np
import vtk


DEFAULT_PLANES = [
    {
        "center": [4.0, 104.0, 120.0],
        "norm": [0.8728715609439696, 0.2182178902359924, 0.4364357804719848],
    },
    {
        "center": [55.0, 143.0, 95.0],
        "norm": [0.08908708, -0.4454354, 0.89087081],
    },
]


def parse_plane(value):
    try:
        center_text, normal_text = value.split(":")
        center = [float(item.strip()) for item in center_text.split(",")]
        normal = [float(item.strip()) for item in normal_text.split(",")]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Expected plane as cx,cy,cz:nx,ny,nz.") from exc

    if len(center) != 3 or len(normal) != 3:
        raise argparse.ArgumentTypeError("Expected plane as cx,cy,cz:nx,ny,nz.")
    return {"center": center, "norm": normal}


def rotation_from_z(normal):
    z_axis = np.array([0.0, 0.0, 1.0])
    normal = np.asarray(normal, dtype=float)
    normal_norm = np.linalg.norm(normal)
    if normal_norm == 0:
        raise ValueError("Plane normal must not be the zero vector.")

    normal = normal / normal_norm
    dot = float(np.clip(np.dot(z_axis, normal), -1.0, 1.0))
    rotation_angle = np.degrees(np.arccos(dot))
    rotation_axis = np.cross(z_axis, normal)

    if np.linalg.norm(rotation_axis) <= 1e-6:
        if dot < 0:
            return rotation_angle, np.array([1.0, 0.0, 0.0])
        return 0.0, z_axis

    return rotation_angle, rotation_axis / np.linalg.norm(rotation_axis)

def create_plane(width, center, normal):
    plane = vtk.vtkPlaneSource()
    plane.SetOrigin(-width / 2, -width / 2, 0)
    plane.SetPoint1(width / 2, -width / 2, 0)
    plane.SetPoint2(-width / 2, width / 2, 0)
    plane.SetResolution(1, 1)

    plane_mapper = vtk.vtkPolyDataMapper()
    plane_mapper.SetInputConnection(plane.GetOutputPort())

    plane_actor = vtk.vtkActor()
    plane_actor.SetMapper(plane_mapper)
    plane_actor.SetPosition(center)

    rotation_angle, rotation_axis = rotation_from_z(normal)
    if rotation_angle:
        plane_actor.RotateWXYZ(rotation_angle, rotation_axis[0], rotation_axis[1], rotation_axis[2])

    plane_actor.GetProperty().SetColor(1.0, 1.0, 0.0)
    plane_actor.GetProperty().SetOpacity(0.5)

    return plane_actor

def display_planes(width, center_norm_dict_list, input_stl_file):
    input_path = Path(input_stl_file).expanduser()
    if not input_path.is_file():
        raise FileNotFoundError(f"Input STL file not found: {input_path}")

    renderer = vtk.vtkRenderer()
    render_window = vtk.vtkRenderWindow()
    render_window.SetWindowName("Tumor cut-plane preview")
    render_window.AddRenderer(renderer)
    render_window_interactor = vtk.vtkRenderWindowInteractor()
    render_window_interactor.SetRenderWindow(render_window)

    for item in center_norm_dict_list:
        center = item["center"]
        norm = item["norm"]
        plane_actor = create_plane(width, center, norm)
        renderer.AddActor(plane_actor)

    stl_reader = vtk.vtkSTLReader()
    stl_reader.SetFileName(str(input_path))

    stl_mapper = vtk.vtkPolyDataMapper()
    stl_mapper.SetInputConnection(stl_reader.GetOutputPort())

    stl_actor = vtk.vtkActor()
    stl_actor.SetMapper(stl_mapper)
    renderer.AddActor(stl_actor)

    renderer.SetBackground(0.1, 0.1, 0.1)
    renderer.ResetCamera()

    render_window.Render()
    render_window_interactor.Start()


def main():
    parser = argparse.ArgumentParser(description="Render a convex hull with one or more cut planes.")
    parser.add_argument("input_stl", nargs="?", default="tumor_hull.stl", help="Input convex-hull STL file.")
    parser.add_argument("--width", type=float, default=100.0, help="Plane width.")
    parser.add_argument(
        "--plane",
        action="append",
        type=parse_plane,
        help="Plane as cx,cy,cz:nx,ny,nz. May be passed more than once.",
    )
    args = parser.parse_args()
    display_planes(args.width, args.plane or DEFAULT_PLANES, args.input_stl)


if __name__ == "__main__":
    main()
