# tumor-cut-plane-show
骨肿瘤切割平面算法展示

- `nii_split.py` 用于 SegmentationCT.nii 的图像拆分，拆分后的图像将存储在 `SegmentationCT` 文件夹
- `nii_split2.py` 用于 CT.nii 的图像拆分，拆分后的图像将存储在 `CT` 文件夹
- `merge_image.py` 用于合并 `SegmentationCT` 以及 `CT` 中的图像，用红色标出肿瘤位置
- `convex_hull.py` 用于对 `tumor.stl` 计算三维凸包，并存储进 `tumor_hull.stl`
- `vtk_show_tumor.py` 使用 vtk 展示骨肿瘤以及骨信息
- `cut_plane.py` 给定凸壳模型给定支撑向量，计算支撑平面
- `show_plane.py` 将若干个支撑平面以及凸壳模型共同显示在同一个场景下
- `key_press_vtk.py` 在 vtk 下测试键盘事件禁用鼠标事件
- `show_all.py` 支持键盘控制平面移动的骨骼、肿瘤、切平面的同时显示