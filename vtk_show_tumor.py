import argparse
from pathlib import Path

import vtk

def read_and_display_stl(file_paths):
    missing_files = [str(Path(file_path).expanduser()) for file_path in file_paths if not Path(file_path).expanduser().is_file()]
    if missing_files:
        raise FileNotFoundError(f"STL file(s) not found: {', '.join(missing_files)}")

    renderer = vtk.vtkRenderer()
    render_window = vtk.vtkRenderWindow()
    render_window.SetWindowName("Tumor STL preview")
    render_window.AddRenderer(renderer)

    render_window_interactor = vtk.vtkRenderWindowInteractor()
    render_window_interactor.SetRenderWindow(render_window)

    for idx, file_path in enumerate(file_paths):
        reader = vtk.vtkSTLReader()
        reader.SetFileName(str(Path(file_path).expanduser()))

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(reader.GetOutputPort())

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)

        if idx == 0:
            actor.GetProperty().SetColor(1.0, 1.0, 1.0)
            actor.GetProperty().SetOpacity(0.5)
        elif idx == 1:
            actor.GetProperty().SetColor(1.0, 0.0, 0.0)
            actor.GetProperty().SetOpacity(0.5)

        renderer.AddActor(actor)

    renderer.SetBackground(0.1, 0.1, 0.1)
    renderer.ResetCamera()

    render_window.Render()
    render_window_interactor.Start()


def main():
    parser = argparse.ArgumentParser(description="Render bone and tumor STL files with VTK.")
    parser.add_argument("stl_files", nargs="*", default=["output.stl", "tumor.stl"], help="STL files to render.")
    args = parser.parse_args()
    read_and_display_stl(args.stl_files)


if __name__ == "__main__":
    main()
