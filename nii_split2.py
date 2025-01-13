import nibabel as nib
import numpy as np
from PIL import Image
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 读取 NIfTI 文件
nii_file_path = '../CT.nii'  # 替换为你的 NIfTI 文件路径
nii_img = nib.load(nii_file_path)

# 获取图像数据
data = nii_img.get_fdata()

# 创建输出目录
output_dir = 'CT'
os.makedirs(output_dir, exist_ok=True)

# 遍历每个切片并保存为图像
for i in range(data.shape[2]):  # 假设 Z 轴是切片的轴
    slice_data = data[:, :, i]
    
    # 将切片数据归一化到 0-255
    slice_data = (slice_data - np.min(slice_data)) / (np.max(slice_data) - np.min(slice_data)) * 255
    slice_data = slice_data.astype(np.uint8)

    # 创建图像并保存
    img = Image.fromarray(slice_data)
    img.save(os.path.join(output_dir, f'slice_{i:03d}.png'))

print(f"已将切片保存到目录: {output_dir}")