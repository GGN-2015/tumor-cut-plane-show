import numpy as np
from stl import mesh
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def find_tangent_planes(input_stl, normal_vector):
    # 读取 STL 文件
    stl_mesh = mesh.Mesh.from_file(input_stl)

    # 提取顶点
    points = np.array(stl_mesh.vectors).reshape(-1, 3)

    # 计算凸壳的中心
    center = np.mean(points, axis=0)

    # 规范化法向量
    normal_vector = normal_vector / np.linalg.norm(normal_vector)

    # 计算与法向量垂直的平面
    # 假设平面方程为 Ax + By + Cz + D = 0
    # D = - (Ax0 + By0 + Cz0)
    # 这里我们将 D 设置为与中心的距离
    distances = np.dot(points - center, normal_vector)
    
    # 找到两个最大的距离对应的点
    min_distance_index = np.argmin(distances)
    max_distance_index = np.argmax(distances)

    # 计算两个平面方程的 D 值
    d1 = -np.dot(normal_vector, points[min_distance_index])
    d2 = -np.dot(normal_vector, points[max_distance_index])

    # 返回平面方程的参数
    return (normal_vector, d1, points[min_distance_index]), (normal_vector, d2, points[max_distance_index])

# 使用示例
input_stl_file = '../tumor_hull.stl'  # 替换为输入 STL 文件的路径
normal_vector = np.array([0.1, -0.5, 1])  # 替换为所需的法向量

plane1, plane2 = find_tangent_planes(input_stl_file, normal_vector)
print(plane1) # 只关心最小坐标值