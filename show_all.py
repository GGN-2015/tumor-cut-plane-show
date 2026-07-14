import argparse
import math
from pathlib import Path

import numpy as np
import vtk

from cut_plane import find_tangent_planes

def rotate_vector_z(vector, alpha_rad):
    rotation_matrix = np.array([
        [np.cos(alpha_rad), -np.sin(alpha_rad), 0],
        [np.sin(alpha_rad), np.cos(alpha_rad), 0],
        [0, 0, 1]
    ])
    return np.dot(rotation_matrix, vector)

def rotate_vector_x(vector, alpha_rad):
    rotation_matrix = np.array([
        [1, 0, 0],
        [0, np.cos(alpha_rad), -np.sin(alpha_rad)],
        [0, np.sin(alpha_rad), np.cos(alpha_rad)],
    ])
    return np.dot(rotation_matrix, vector)


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

class VTKApp:
    def __init__(self, hull_file: str, width: int, stl_file_list):
        self.support_vector = np.array([1.0, 0.0, 0.0])

        self.hull_file = Path(hull_file).expanduser()
        self.stl_file_list = [Path(file_path).expanduser() for file_path in stl_file_list]
        self.validate_input_files()

        self.renderer = vtk.vtkRenderer()
        self.render_window = vtk.vtkRenderWindow()
        self.render_window.SetWindowName("Tumor cut-plane explorer")
        self.render_window.AddRenderer(self.renderer)
        self.render_window_interactor = vtk.vtkRenderWindowInteractor()
        self.render_window_interactor.SetRenderWindow(self.render_window)

        self.plane = vtk.vtkPlaneSource()
        self.plane.SetOrigin(-width / 2, -width / 2, 0)
        self.plane.SetPoint1(width / 2, -width / 2, 0)
        self.plane.SetPoint2(-width / 2, width / 2, 0)
        self.plane.SetResolution(1, 1)

        self.plane_mapper = vtk.vtkPolyDataMapper()
        self.plane_mapper.SetInputConnection(self.plane.GetOutputPort())

        self.plane_actor = vtk.vtkActor()
        self.plane_actor.SetMapper(self.plane_mapper)

        self.plane_actor.GetProperty().SetColor(1.0, 1.0, 0.0)
        self.plane_actor.GetProperty().SetOpacity(0.9)
        self.plane_actor.GetProperty().SetRepresentationToSurface()
        self.renderer.AddActor(self.plane_actor)

        self.render_window_interactor.AddObserver("KeyPressEvent", self.on_key_press)

        self.read_and_display_stl(self.stl_file_list)

        self.renderer.SetBackground(0.1, 0.2, 0.4)
        self.renderer.ResetCamera()

        self.reset_plane_coord()

    def validate_input_files(self):
        missing_files = []
        if not self.hull_file.is_file():
            missing_files.append(str(self.hull_file))
        missing_files.extend(str(file_path) for file_path in self.stl_file_list if not file_path.is_file())
        if missing_files:
            raise FileNotFoundError(f"Required STL file(s) not found: {', '.join(missing_files)}")

    def start(self):
        self.render_window.Render()
        self.render_window_interactor.Start()

    def read_and_display_stl(self, file_paths):
        for idx, file_path in enumerate(file_paths):
            reader = vtk.vtkSTLReader()
            reader.SetFileName(str(file_path))

            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(reader.GetOutputPort())

            actor = vtk.vtkActor()
            actor.SetMapper(mapper)

            if idx == 0:
                actor.GetProperty().SetColor(1.0, 1.0, 1.0)
                actor.GetProperty().SetOpacity(0.3)
            elif idx == 1:
                actor.GetProperty().SetColor(1.0, 0.0, 0.0)
                actor.GetProperty().SetOpacity(0.2)

            actor.GetProperty().SetRepresentationToSurface()
            self.renderer.AddActor(actor)

    def reset_plane_coord(self):
        point1, _ = find_tangent_planes(self.hull_file, self.support_vector)
        normal, _, center = point1
        self.support_vector = normal

        self.plane_actor.SetPosition(center)
        self.plane_actor.SetOrientation(0.0, 0.0, 0.0)

        rotation_angle, rotation_axis = rotation_from_z(normal)
        if rotation_angle:
            self.plane_actor.RotateWXYZ(rotation_angle, rotation_axis[0], rotation_axis[1], rotation_axis[2])
            self.plane_actor.GetProperty().SetRepresentationToSurface()

    def on_key_press(self, obj, event):
        key = obj.GetKeySym()
        if key == 'Up':
            self.support_vector = rotate_vector_z(self.support_vector, 1 / 180 * math.pi)
        elif key == 'Down':
            self.support_vector = rotate_vector_z(self.support_vector, -1 / 180 * math.pi)
        elif key == 'Left':
            self.support_vector = rotate_vector_x(self.support_vector, 1 / 180 * math.pi)
        elif key == 'Right':
            self.support_vector = rotate_vector_x(self.support_vector, -1 / 180 * math.pi)

        self.reset_plane_coord()
        self.render_window.Render()


def main():
    parser = argparse.ArgumentParser(
        description="Render bone, tumor, and an interactive tangent cut plane. Use arrow keys to rotate the plane."
    )
    parser.add_argument("--hull", default="tumor_hull.stl", help="Convex-hull STL file.")
    parser.add_argument("--width", type=float, default=100.0, help="Cut-plane width.")
    parser.add_argument(
        "--stl",
        action="append",
        default=None,
        help="STL file to render. Pass twice for bone and tumor. Defaults to output.stl and tumor.stl.",
    )
    args = parser.parse_args()
    app = VTKApp(hull_file=args.hull, width=args.width, stl_file_list=args.stl or ["output.stl", "tumor.stl"])
    app.start()


if __name__ == "__main__":
    main()
