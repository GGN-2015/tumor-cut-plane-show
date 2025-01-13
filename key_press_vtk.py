import vtk

class VTKApp:
    def __init__(self):
        # 创建一个渲染窗口
        self.renderer = vtk.vtkRenderer()
        self.render_window = vtk.vtkRenderWindow()
        self.render_window.AddRenderer(self.renderer)
        self.render_window_interactor = vtk.vtkRenderWindowInteractor()
        self.render_window_interactor.SetRenderWindow(self.render_window)

        # 创建一个简单的立方体
        self.cube = vtk.vtkCubeSource()
        self.cube_mapper = vtk.vtkPolyDataMapper()
        self.cube_mapper.SetInputConnection(self.cube.GetOutputPort())
        self.cube_actor = vtk.vtkActor()
        self.cube_actor.SetMapper(self.cube_mapper)
        self.renderer.AddActor(self.cube_actor)

        # 设置相机
        self.renderer.SetBackground(0.1, 0.2, 0.4)
        self.renderer.ResetCamera()

        # 设置键盘事件
        self.render_window_interactor.AddObserver("KeyPressEvent", self.on_key_press)

        # 禁用鼠标事件
        self.render_window_interactor.SetInteractorStyle(vtk.vtkInteractorStyleImage())

        # 开始渲染
        self.render_window.Render()
        self.render_window_interactor.Start()

    def on_key_press(self, obj, event):
        key = obj.GetKeySym()
        if key == 'w':
            self.cube_actor.RotateX(5)
        elif key == 's':
            self.cube_actor.RotateX(-5)
        elif key == 'a':
            self.cube_actor.RotateY(-5)
        elif key == 'd':
            self.cube_actor.RotateY(5)
        self.render_window.Render()

if __name__ == "__main__":
    app = VTKApp()