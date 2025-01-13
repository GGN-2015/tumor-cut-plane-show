import vtk
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 创建 STL 读取器
reader = vtk.vtkSTLReader()
reader.SetFileName("../output.stl")  # 替换为你的 STL 文件路径

# 创建映射器
mapper = vtk.vtkPolyDataMapper()
mapper.SetInputConnection(reader.GetOutputPort())

# 创建演员
actor = vtk.vtkActor()
actor.SetMapper(mapper)

# 创建渲染器、渲染窗口和交互器
renderer = vtk.vtkRenderer()
renderWindow = vtk.vtkRenderWindow()
renderWindow.AddRenderer(renderer)

renderWindowInteractor = vtk.vtkRenderWindowInteractor()
renderWindowInteractor.SetRenderWindow(renderWindow)

# 添加演员到渲染器
renderer.AddActor(actor)
renderer.SetBackground(0.1, 0.1, 0.1)  # 设置背景色为深灰色

# 启动渲染循环
renderWindow.Render()
renderWindowInteractor.Start()