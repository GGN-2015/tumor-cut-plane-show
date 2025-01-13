import vtk
from cut_plane import find_tangent_planes
import numpy as np
import math

def rotate_vector_z(vector, alpha_rad):
    # 创建旋转矩阵
    rotation_matrix = np.array([
        [np.cos(alpha_rad), -np.sin(alpha_rad), 0],
        [np.sin(alpha_rad), np.cos(alpha_rad), 0],
        [0, 0, 1]
    ])
    
    # 进行旋转
    rotated_vector = np.dot(rotation_matrix, vector)
    return rotated_vector

def rotate_vector_x(vector, alpha_rad):
    # 创建旋转矩阵
    rotation_matrix = np.array([
        [1, 0, 0],
        [0, np.cos(alpha_rad), -np.sin(alpha_rad)],
        [0, np.sin(alpha_rad), np.cos(alpha_rad)],
    ])
    
    # 进行旋转
    rotated_vector = np.dot(rotation_matrix, vector)
    return rotated_vector

class VTKApp:
    def __init__(self, hull_file: str, width:int, stl_file_list):
        # 当前支撑向量方向
        self.support_vector = np.array([1, 0, 0])
        self.norm_now = np.array([0, 0, 1])

        # 凸壳文件
        self.hull_file = hull_file

        # 创建一个渲染窗口
        self.renderer = vtk.vtkRenderer()
        self.render_window = vtk.vtkRenderWindow()
        self.render_window.AddRenderer(self.renderer)
        self.render_window_interactor = vtk.vtkRenderWindowInteractor()
        self.render_window_interactor.SetRenderWindow(self.render_window)

        # 创建一个平面源
        self.plane = vtk.vtkPlaneSource()
        self.plane.SetOrigin(-width/2, -width/2, 0)  # 平面的一个顶点
        self.plane.SetPoint1(width/2, -width/2, 0)    # 平面另一条边的顶点
        self.plane.SetPoint2(-width/2, width/2, 0)    # 平面另一条边的顶点
        self.plane.SetResolution(1, 1)

        # 创建平面 mapper
        self.plane_mapper = vtk.vtkPolyDataMapper()
        self.plane_mapper.SetInputConnection(self.plane.GetOutputPort())

        # 创建平面 actor
        self.plane_actor = vtk.vtkActor()
        self.plane_actor.SetMapper(self.plane_mapper)

        self.plane_actor.GetProperty().SetColor(1.0, 1.0, 0.0)  # 半透明黄色
        self.plane_actor.GetProperty().SetOpacity(0.9)  # 半透明
        self.plane_actor.GetProperty().SetRepresentationToSurface()
        self.renderer.AddActor(self.plane_actor)

        # 设置键盘事件
        self.render_window_interactor.AddObserver("KeyPressEvent", self.on_key_press)

        # 禁用鼠标事件
        # self.render_window_interactor.SetInteractorStyle(vtk.vtkInteractorStyleImage())

        # 添加 stl 演员
        self.read_and_display_stl(stl_file_list)

        # 设置相机
        self.renderer.SetBackground(0.1, 0.2, 0.4)
        self.renderer.ResetCamera()

        # 开始渲染
        self.reset_plane_coord()
        self.render_window.Render()
        self.render_window_interactor.Start()

    def read_and_display_stl(self, file_paths):
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
                actor.GetProperty().SetOpacity(0.3)  # 半透明
            elif idx == 1:  # 第二个模型
                actor.GetProperty().SetColor(1.0, 0.0, 0.0)  # 半透明红色
                actor.GetProperty().SetOpacity(0.2)  # 半透明

            # 将演员添加到渲染器
            actor.GetProperty().SetRepresentationToSurface()
            self.renderer.AddActor(actor)

    def reset_plane_coord(self):
        point1, _ = find_tangent_planes(self.hull_file, self.support_vector)
        _, _, center = point1

        # 设置平面的中心点
        self.plane_actor.SetPosition(center)

        # 计算平面旋转角度
        if np.all(self.support_vector == 0):  # 确保法向量不为零
            self.support_vector = self.norm_now
        rotation_axis = np.cross(self.norm_now, self.support_vector)
        rotation_angle = np.arccos(np.dot(self.norm_now, self.support_vector) / (np.linalg.norm(self.norm_now) * np.linalg.norm(self.support_vector))) * (180.0 / np.pi)

        # 旋转平面
        if np.linalg.norm(rotation_axis) > 1e-6:  # 检查是否需要旋转
            rotation_axis = rotation_axis / np.linalg.norm(rotation_axis)
            # 修正 RotateWXYZ 的调用，确保传入 4 个参数
            self.plane_actor.RotateWXYZ(rotation_angle, rotation_axis[0], rotation_axis[1], rotation_axis[2])
            self.plane_actor.GetProperty().SetRepresentationToSurface()

        # 记录新的法向量
        self.norm_now = self.support_vector

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



if __name__ == "__main__":
    app = VTKApp(hull_file="../tumor_hull.stl", width=100, stl_file_list=["../output.stl", "../tumor.stl"])