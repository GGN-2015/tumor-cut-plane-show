import numpy as np
from stl import mesh
from scipy.spatial import ConvexHull
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def generate_convex_hull(input_stl, output_stl):
    # 读取 STL 文件
    stl_mesh = mesh.Mesh.from_file(input_stl)

    # 提取顶点
    points = np.array(stl_mesh.vectors).reshape(-1, 3)

    # 计算凸包
    hull = ConvexHull(points)

    # 创建一个新的 STL mesh 来保存凸包
    hull_mesh = mesh.Mesh(np.zeros(hull.simplices.shape[0], dtype=mesh.Mesh.dtype))

    for i, simplex in enumerate(hull.simplices):
        for j in range(3):
            hull_mesh.vectors[i][j] = points[simplex[j], :]

    # 保存凸包 STL 文件
    hull_mesh.save(output_stl)
    print(f"凸包已保存到: {output_stl}")

# 使用示例
input_stl_file = '../tumor.stl'  # 替换为输入 STL 文件的路径
output_stl_file = '../tumor_hull.stl'  # 替换为输出 STL 文件的路径

generate_convex_hull(input_stl_file, output_stl_file)