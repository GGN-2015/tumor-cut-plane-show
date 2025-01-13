from tqdm import tqdm
from PIL import Image
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def get_mid_color(c1, c2):
    return tuple([round((c1[i] + c2[i]) / 2) for i in range(len(c1))])

def overlay_images(folder_a, folder_b, output_folder):
    # 创建输出文件夹
    os.makedirs(output_folder, exist_ok=True)

    # 遍历文件夹 A 中的 PNG 文件
    for filename in tqdm(list(os.listdir(folder_a))):
        if filename.endswith('.png'):
            # 构建完整路径
            file_a_path = os.path.join(folder_a, filename)
            file_b_path = os.path.join(folder_b, filename)
            
            # 确保文件夹 B 中存在对应的文件
            if os.path.isfile(file_b_path):
                # 打开图片
                img_a = Image.open(file_a_path).convert("RGB")
                img_b = Image.open(file_b_path).convert("RGB")

                # 创建一个新的图像用于合并
                merged_img = Image.new("RGB", img_a.size)

                # 遍历每个像素
                for x in range(img_a.width):
                    for y in range(img_a.height):
                        a_pixel = img_a.getpixel((x, y))
                        b_pixel = img_b.getpixel((x, y))

                        # 检查文件夹 B 中的像素是否为白色
                        if b_pixel[0] > 240 and b_pixel[1] > 240 and b_pixel[2] > 240:  # 白色区域
                            # 使用半透明红色覆盖
                            merged_img.putpixel((x, y), get_mid_color(a_pixel, (255, 0, 0)))  # 半透明红色
                        else:
                            # 保持文件夹 A 中的像素
                            merged_img.putpixel((x, y), a_pixel)

                # 保存合并后的图像
                merged_img.save(os.path.join(output_folder, filename))

    print(f"合并完成，结果保存在 '{output_folder}' 文件夹中。")

# 使用示例
folder_a = 'CT'  # 替换为文件夹 A 的路径
folder_b = 'SegmentationCT'  # 替换为文件夹 B 的路径
output_folder = 'merged'  # 替换为输出文件夹的路径

overlay_images(folder_a, folder_b, output_folder)