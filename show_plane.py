import vtk
from stl import mesh
import numpy as np
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def create_plane(width, center, normal):
    # 创建一个平面源
    plane = vtk.vtkPlaneSource()
    plane.SetOrigin(-width/2, -width/2, 0)  # 平面的一个顶点
    plane.SetPoint1(width/2, -width/2, 0)    # 平面另一条边的顶点
    plane.SetPoint2(-width/2, width/2, 0)    # 平面另一条边的顶点
    plane.SetResolution(1, 1)

    # 创建平面 mapper
    plane_mapper = vtk.vtkPolyDataMapper()
    plane_mapper.SetInputConnection(plane.GetOutputPort())

    # 创建平面 actor
    plane_actor = vtk.vtkActor()
    plane_actor.SetMapper(plane_mapper)

    # 设置平面的中心点
    plane_actor.SetPosition(center)

    # 计算平面旋转角度
    z_axis = np.array([0, 0, 1])  # 默认法向量
    if np.all(normal == 0):  # 确保法向量不为零
        normal = z_axis
    rotation_axis = np.cross(z_axis, normal)
    rotation_angle = np.arccos(np.dot(z_axis, normal) / (np.linalg.norm(z_axis) * np.linalg.norm(normal))) * (180.0 / np.pi)

    # 旋转平面
    if np.linalg.norm(rotation_axis) > 1e-6:  # 检查是否需要旋转
        rotation_axis = rotation_axis / np.linalg.norm(rotation_axis)
        # 修正 RotateWXYZ 的调用，确保传入 4 个参数
        plane_actor.RotateWXYZ(rotation_angle, rotation_axis[0], rotation_axis[1], rotation_axis[2])

    plane_actor.GetProperty().SetColor(1.0, 1.0, 0.0)  # 半透明黄色
    plane_actor.GetProperty().SetOpacity(0.5)  # 半透明

    return plane_actor

def main(width, center_norm_dict_list, input_stl_file):
    # 创建 VTK 渲染器
    renderer = vtk.vtkRenderer()
    render_window = vtk.vtkRenderWindow()
    render_window.AddRenderer(renderer)
    render_window_interactor = vtk.vtkRenderWindowInteractor()
    render_window_interactor.SetRenderWindow(render_window)

    # 创建半透明平面
    for item in center_norm_dict_list:
        center = item["center"]
        norm = item["norm"]
        plane_actor = create_plane(width, center, norm)

        # 添加平面到渲染器
        renderer.AddActor(plane_actor)

    # 读取 STL 文件
    stl_reader = vtk.vtkSTLReader()
    stl_reader.SetFileName(input_stl_file)

    # 创建一个 mapper
    stl_mapper = vtk.vtkPolyDataMapper()
    stl_mapper.SetInputConnection(stl_reader.GetOutputPort())

    # 创建一个 actor
    stl_actor = vtk.vtkActor()
    stl_actor.SetMapper(stl_mapper)

    # 添加 actor 到渲染器
    renderer.AddActor(stl_actor)

    # 设置渲染器背景色
    renderer.SetBackground(0.1, 0.1, 0.1)  # 深灰色背景

    # 设置视角
    renderer.ResetCamera()

    # 开始渲染
    render_window.Render()
    render_window_interactor.Start()

# 使用示例
width = 100
main(width, [
    {
        "center": [  4., 104., 120.],
        "norm": [0.8728715609439696, 0.2182178902359924, 0.4364357804719848]
    },
    {
        "center": [ 55., 143.,  95.],
        "norm": [ 0.08908708, -0.4454354 ,  0.89087081]
    }
], "../tumor_hull.stl")