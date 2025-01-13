import vtk
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def read_and_display_stl(file_paths):
    # 创建渲染器、渲染窗口和交互器
    renderer = vtk.vtkRenderer()
    render_window = vtk.vtkRenderWindow()
    render_window.AddRenderer(renderer)

    render_window_interactor = vtk.vtkRenderWindowInteractor()
    render_window_interactor.SetRenderWindow(render_window)

    for idx, file_path in enumerate(file_paths):
        # 创建 STL 读取器
        reader = vtk.vtkSTLReader()
        reader.SetFileName(file_path)

        # 创建映射器
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(reader.GetOutputPort())

        # 创建演员
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)

        # 设置颜色和透明度
        if idx == 0:  # 第一个模型
            actor.GetProperty().SetColor(1.0, 1.0, 1.0)  # 半透明白色
            actor.GetProperty().SetOpacity(0.5)  # 半透明
        elif idx == 1:  # 第二个模型
            actor.GetProperty().SetColor(1.0, 0.0, 0.0)  # 半透明红色
            actor.GetProperty().SetOpacity(0.5)  # 半透明

        # 将演员添加到渲染器
        renderer.AddActor(actor)

    # 设置背景色
    renderer.SetBackground(0.1, 0.1, 0.1)  # 深灰色背景

    # 启动渲染循环
    render_window.Render()
    render_window_interactor.Start()

# STL 文件路径
stl_files = [
    '../output.stl',   # 替换为第一个 STL 文件的路径
    '../tumor.stl',  # 替换为第二个 STL 文件的路径
]

read_and_display_stl(stl_files)