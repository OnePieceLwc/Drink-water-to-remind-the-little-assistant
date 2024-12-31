import sys
from PyQt5 import QtWidgets, QtGui, QtCore
import winreg  # 添加到文件顶部的导入语句中
import os

def get_resource_path(relative_path):
    """获取资源文件的绝对路径"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 创建临时文件夹，将路径存储在 _MEIPASS 中
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

class WaterReminderApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("喝水提醒小助手")
        
        # 初始化开机自启动相关的属性
        self.startup_reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        self.app_name = "WaterReminder"
        self.app_path = sys.argv[0]
        
        # 获取当前屏幕，支持多屏和平板
        screen = QtWidgets.QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        available_geometry = screen.availableGeometry()
        self.screen_width = screen_geometry.width()
        self.screen_height = screen_geometry.height()
        
        # 计算任务栏高度，如果是平板可能没有任务栏
        taskbar_height = max(screen_geometry.height() - available_geometry.height(), 0)
        
        # 设置窗口位置，考虑平板屏幕
        self.setGeometry(
            0,  
            self.screen_height - taskbar_height - 60,  # 增加高度以适应触摸
            self.screen_width,  
            60  # 增加高度以适应触摸
        )
        
        # 修改窗口属性以支持触摸
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        
        # 只在非触摸设备上启用鼠标穿透
        if not self.is_touch_device():
            self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        
        # 初始化托盘图标
        self.icon_path = get_resource_path("喝水提醒小助手.ico")
        self.setup_tray_icon()
        
        # 初始化喝水计数器和计时器
        self.water_count = 0
        self.progress_value = 0
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_progress)
        self.reminder_interval = 10800  # 3小时 = 3 * 60 * 60 秒
        self.timer.start(100)  # 每0.1秒更新一次进度条
        
        # 美化进度条
        self.progress_bar = QtWidgets.QProgressBar(self)
        self.progress_bar.setGeometry(10, 5, screen_geometry.width() - 170, 30)  # 调整进度条宽度
        self.progress_bar.setTextVisible(False)  # 隐藏进度条文字
        self.update_progress_bar_style(0.5)
        
        # 美化计数器标签
        self.counter_label = QtWidgets.QLabel(self)
        self.counter_label.setGeometry(screen_geometry.width() - 150, 5, 140, 30)  # 增加宽度到140，左移20像素
        self.counter_label.setStyleSheet("""
            QLabel {
                color: #2196F3;
                background-color: rgba(255, 255, 255, 0.85);
                border-radius: 15px;
                padding: 0 15px;
                font-size: 14px;
                font-weight: bold;
                font-family: 'Microsoft YaHei', Arial;
            }
        """)
        self.update_counter_display()
        
        # 设置午夜重置计时器
        self.reset_timer = QtCore.QTimer(self)
        self.reset_timer.timeout.connect(self.check_midnight_reset)
        self.reset_timer.start(60000)  # 每分钟检查一次
        
        # 显示选项面板
        self.show_options()
        self.show()

    def setup_tray_icon(self):
        """设置托盘图标"""
        self.tray_icon = QtWidgets.QSystemTrayIcon(self)
        self.tray_icon.setIcon(QtGui.QIcon(self.icon_path))
        
        # 创建托盘菜单
        tray_menu = QtWidgets.QMenu()
        
        # 基础设置子菜单
        settings_menu = QtWidgets.QMenu("基础设置", tray_menu)
        
        # 添加提醒间隔设置选项
        interval_action = settings_menu.addAction("提醒间隔")
        interval_action.triggered.connect(self.show_interval_dialog)
        
        # 添加提醒文字设置选项
        text_action = settings_menu.addAction("提醒文字")
        text_action.triggered.connect(self.show_text_dialog)
        
        # 添加透明度设置选项
        opacity_action = settings_menu.addAction("透明度")
        opacity_action.triggered.connect(self.show_opacity_dialog)
        
        # 添加开机自启动选项
        self.startup_action = settings_menu.addAction("开机自启")
        self.startup_action.setCheckable(True)  # 使其可以切换选中状态
        self.startup_action.setChecked(self.is_auto_start())  # 设置初始状态
        self.startup_action.triggered.connect(self.toggle_auto_start)
        
        # 将基础设置子菜单添加到主菜单
        tray_menu.addMenu(settings_menu)
        
        # 添加分隔线
        tray_menu.addSeparator()
        
        # 添加退出选项
        quit_action = tray_menu.addAction("退出")
        quit_action.triggered.connect(self.quit_application)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def quit_application(self):
        """安全退出应用程序"""
        self.tray_icon.hide()  # 隐藏托盘图标
        QtWidgets.QApplication.quit()

    def update_progress_bar_style(self, opacity):
        """更新进度条样式"""
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: rgba(255, 255, 255, {opacity});
                border-radius: 15px;
                text-align: center;
                border: none;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                          stop:0 #2196F3, stop:1 #00BCD4);
                border-radius: 15px;
            }}
        """)

    def show_options(self):
        options_window = QtWidgets.QDialog(self)
        options_window.setWindowTitle("设置选项")
        options_window.setFixedSize(500, 600)  # 增加窗口尺寸
        options_window.setWindowIcon(QtGui.QIcon(self.icon_path))
        
        # 更新窗口样式
        options_window.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
                border-radius: 10px;
            }
            QLabel {
                color: #333333;
                font-size: 15px;
                font-family: 'Microsoft YaHei', Arial;
                margin-top: 10px;
            }
            QSpinBox, QDoubleSpinBox, QLineEdit {
                padding: 10px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                background: white;
                font-size: 14px;
                min-height: 25px;
                min-width: 200px;
            }
            QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus {
                border-color: #2196F3;
            }
        """)

        layout = QtWidgets.QVBoxLayout(options_window)
        layout.setSpacing(20)  # 增加间距
        layout.setContentsMargins(30, 30, 30, 30)  # 增加边距

        # 调整图标和标题
        header_layout = QtWidgets.QHBoxLayout()
        icon_label = QtWidgets.QLabel()
        icon_label.setPixmap(QtGui.QPixmap(self.icon_path).scaled(80, 80, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))  # 增大图标
        header_layout.addWidget(icon_label)
        
        title_label = QtWidgets.QLabel("喝水提醒小助手设置")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2196F3;
            }
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # 分隔线
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setStyleSheet("background-color: #e0e0e0; min-height: 2px;")
        layout.addWidget(line)

        # 表单布局
        form_layout = QtWidgets.QFormLayout()
        form_layout.setSpacing(20)  # 增加表单项间距
        form_layout.setLabelAlignment(QtCore.Qt.AlignRight)  # 标签右对齐
        form_layout.setFormAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)  # 输入框左对齐

        # 喝水提醒频率设置
        self.frequency_label = QtWidgets.QLabel("喝水提醒频率：")
        self.frequency_input = QtWidgets.QDoubleSpinBox()  # 改用 QDoubleSpinBox 支持小数
        self.frequency_input.setRange(0.5, 4)  # 范围从0.5小时到4小时
        self.frequency_input.setSingleStep(0.5)  # 步长为0.5小时
        self.frequency_input.setValue(3)  # 默认3小时
        self.frequency_input.setSuffix(" 小时")
        form_layout.addRow(self.frequency_label, self.frequency_input)

        # 提醒文字设置
        self.reminder_text_label = QtWidgets.QLabel("提醒文字：")
        self.reminder_text_input = QtWidgets.QLineEdit("该喝水了！")
        form_layout.addRow(self.reminder_text_label, self.reminder_text_input)

        # 窗口透明度设置
        self.transparency_label = QtWidgets.QLabel("窗口透明度：")
        self.transparency_input = QtWidgets.QDoubleSpinBox()
        self.transparency_input.setRange(0.1, 1.0)
        self.transparency_input.setSingleStep(0.1)
        self.transparency_input.setValue(0.8)
        form_layout.addRow(self.transparency_label, self.transparency_input)

        # 进度条透明度设置
        self.progress_opacity_label = QtWidgets.QLabel("进度条透明度：")
        self.progress_opacity_input = QtWidgets.QDoubleSpinBox()
        self.progress_opacity_input.setRange(0.1, 1.0)
        self.progress_opacity_input.setSingleStep(0.1)
        self.progress_opacity_input.setValue(0.5)
        form_layout.addRow(self.progress_opacity_label, self.progress_opacity_input)

        layout.addLayout(form_layout)
        
        # 调整说明文本
        help_text = QtWidgets.QLabel(
            "提示：\n"
            "• 透明度范围为0.1-1.0，数值越大越不透明\n"
            "• 默认提醒间隔为3小时，建议设置在0.5-4小时之间\n"
            "• 可以随时通过托盘图标右键菜单修改设置"
        )
        help_text.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 13px;
                padding: 15px;
                background-color: #e3f2fd;
                border-radius: 8px;
                line-height: 1.5;
            }
        """)
        layout.addWidget(help_text)

        # 调整保存按钮
        save_button = QtWidgets.QPushButton("保存设置")
        save_button.setFixedSize(160, 45)  # 增大按钮尺寸
        save_button.clicked.connect(lambda: self.save_settings(options_window))
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
        """)
        layout.addWidget(save_button, alignment=QtCore.Qt.AlignCenter)

        # 调整输入控件大小以适应触摸
        self.frequency_input.setMinimumHeight(40)
        self.reminder_text_input.setMinimumHeight(40)
        self.transparency_input.setMinimumHeight(40)
        self.progress_opacity_input.setMinimumHeight(40)
        
        # 增加触摸反馈
        save_button.setMinimumSize(180, 60)

        options_window.exec_()

    def update_progress(self):
        """更新进度条"""
        # 如果提醒窗口已经显示，则不再更新进度
        if hasattr(self, 'reminder_window') and self.reminder_window.isVisible():
            return
        
        step = 100 * 0.1 / self.reminder_interval  # 计算每0.1秒应该增加的进度值
        self.progress_value += step
        
        if self.progress_value >= 100:
            self.progress_value = 100
            self.progress_bar.setValue(100)
            self.show_reminder()
        else:
            self.progress_bar.setValue(int(self.progress_value))

    def show_reminder(self):
        """显示提醒窗口，适配触摸设备"""
        if hasattr(self, 'reminder_window') and self.reminder_window.isVisible():
            return
        
        self.reminder_window = QtWidgets.QDialog(self)
        self.reminder_window.setWindowTitle("喝水提醒")
        
        # 适配屏幕尺寸
        self.reminder_window.setGeometry(0, 0, self.screen_width, self.screen_height)
        
        # 设置为非模态
        self.reminder_window.setModal(False)
        
        # 设置整个窗口的背景样式
        self.reminder_window.setStyleSheet("""
            QDialog {
                background-color: rgba(200, 220, 255, 0.1);  /* 非常淡的蓝色背景 */
            }
        """)
        
        # 创建内容容器，居中显示内容
        content_container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(content_container)
        layout.setAlignment(QtCore.Qt.AlignCenter)
        layout.setSpacing(30)

        # 提醒文字
        label = QtWidgets.QLabel(self.reminder_text_input.text())
        label.setStyleSheet("""
            QLabel {
                font-size: 72px;  /* 增大字体 */
                color: #2196F3;
                font-weight: bold;
                font-family: 'Microsoft YaHei', Arial;
                background-color: white;
                padding: 40px 80px;  /* 增大内边距 */
                border-radius: 40px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
        """)
        layout.addWidget(label)

        # 按钮容器
        button_container = QtWidgets.QWidget()
        button_layout = QtWidgets.QHBoxLayout(button_container)
        button_layout.setSpacing(30)

        # 喝水按钮
        yes_button = QtWidgets.QPushButton("喝水")
        yes_button.clicked.connect(self.drink_water)
        yes_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #4CAF50, stop:1 #45A049);
                color: white;
                border: none;
                border-radius: 40px;
                padding: 25px 60px;
                font-size: 28px;
                font-weight: bold;
                font-family: 'Microsoft YaHei', Arial;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #45A049, stop:1 #388E3C);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #388E3C, stop:1 #2E7D32);
                padding: 28px 60px 22px 60px;
            }
        """)
        button_layout.addWidget(yes_button)

        # 稍后按钮
        no_button = QtWidgets.QPushButton("稍后")
        no_button.clicked.connect(self.no_drink)
        no_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #FF5252, stop:1 #F44336);
                color: white;
                border: none;
                border-radius: 40px;
                padding: 25px 60px;
                font-size: 28px;
                font-weight: bold;
                font-family: 'Microsoft YaHei', Arial;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #F44336, stop:1 #D32F2F);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #D32F2F, stop:1 #B71C1C);
                padding: 28px 60px 22px 60px;
            }
        """)
        button_layout.addWidget(no_button)

        layout.addWidget(button_container)

        # 调整按钮大小和样式以适应触摸
        yes_button.setMinimumSize(200, 80)
        no_button.setMinimumSize(200, 80)
        
        # 增加触摸反馈效果
        yes_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #4CAF50, stop:1 #45A049);
                color: white;
                border: none;
                border-radius: 40px;
                padding: 25px 60px;
                font-size: 28px;
                font-weight: bold;
                font-family: 'Microsoft YaHei', Arial;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #45A049, stop:1 #388E3C);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #388E3C, stop:1 #2E7D32);
                padding: 28px 60px 22px 60px;
            }
        """)
        
        no_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #FF5252, stop:1 #F44336);
                color: white;
                border: none;
                border-radius: 40px;
                padding: 25px 60px;
                font-size: 28px;
                font-weight: bold;
                font-family: 'Microsoft YaHei', Arial;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #F44336, stop:1 #D32F2F);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #D32F2F, stop:1 #B71C1C);
                padding: 28px 60px 22px 60px;
            }
        """)

        # 调整提醒文字大小
        label.setStyleSheet("""
            QLabel {
                font-size: 72px;  /* 增大字体 */
                color: #2196F3;
                font-weight: bold;
                font-family: 'Microsoft YaHei', Arial;
                background-color: white;
                padding: 40px 80px;  /* 增大内边距 */
                border-radius: 40px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
        """)

        # 设置主布局
        main_layout = QtWidgets.QVBoxLayout(self.reminder_window)
        main_layout.addWidget(content_container)

        self.reminder_window.show()
        self.reminder_window.windowHandle().setScreen(QtGui.QGuiApplication.primaryScreen())
        self.reminder_window.showFullScreen()

    def drink_water(self):
        """点击喝水按钮的处理函数"""
        self.water_count += 1
        self.update_counter_display()
        self.progress_value = 0  # 重置进度值
        self.progress_bar.setValue(0)
        self.reminder_window.close()
        # 确保计时器在运行
        if not self.timer.isActive():
            self.timer.start(100)

    def save_settings(self, options_window):
        """保存设置"""
        # 将小时转换为秒
        hours = self.frequency_input.value()
        self.reminder_interval = int(hours * 3600)  # 转换为秒
        self.progress_value = 0
        self.progress_bar.setValue(0)
        
        # 更新进度条透明度
        opacity = self.progress_opacity_input.value()
        self.update_progress_bar_style(opacity)
        
        # 更新窗口透明度
        window_opacity = self.transparency_input.value()
        self.setWindowOpacity(window_opacity)
        
        options_window.close()

    def update_counter_display(self):
        """更新计数器显示"""
        self.counter_label.setText(f"💧 今日喝水: {self.water_count}")

    def check_midnight_reset(self):
        current_time = QtCore.QTime.currentTime()
        if current_time.hour() == 0 and current_time.minute() == 0:
            self.water_count = 0
            self.update_counter_display()

    def no_drink(self):
        """点击稍后按钮的处理函数"""
        self.progress_value = 0  # 重置进度值
        self.progress_bar.setValue(0)
        self.reminder_window.close()
        # 确保计时器在运行
        if not self.timer.isActive():
            self.timer.start(100)

    def show_interval_dialog(self):
        """显示提醒间隔设置对话框"""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("设置提醒间隔")
        dialog.setFixedSize(300, 150)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        
        spinbox = QtWidgets.QDoubleSpinBox(dialog)
        spinbox.setRange(0.5, 4)  # 0.5到4小时
        spinbox.setSingleStep(0.5)
        spinbox.setValue(self.reminder_interval / 3600)  # 将秒转换为小时
        spinbox.setSuffix(" 小时")
        
        layout.addWidget(QtWidgets.QLabel("请设置提醒间隔："))
        layout.addWidget(spinbox)
        
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            dialog
        )
        buttons.accepted.connect(lambda: self.save_interval(int(spinbox.value() * 3600), dialog))
        buttons.rejected.connect(dialog.reject)
        
        layout.addWidget(buttons)
        dialog.exec_()

    def show_text_dialog(self):
        """显示提醒文字设置对话框"""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("设置提醒文字")
        dialog.setFixedSize(300, 150)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        
        text_input = QtWidgets.QLineEdit(dialog)
        text_input.setText(self.reminder_text_input.text())
        
        layout.addWidget(QtWidgets.QLabel("请输入提醒文字："))
        layout.addWidget(text_input)
        
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            dialog
        )
        buttons.accepted.connect(lambda: self.save_text(text_input.text(), dialog))
        buttons.rejected.connect(dialog.reject)
        
        layout.addWidget(buttons)
        dialog.exec_()

    def show_opacity_dialog(self):
        """显示透明度设置对话框"""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("设置透明度")
        dialog.setFixedSize(300, 150)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        
        spinbox = QtWidgets.QDoubleSpinBox(dialog)
        spinbox.setRange(0.1, 1.0)
        spinbox.setSingleStep(0.1)
        spinbox.setValue(self.transparency_input.value())
        
        layout.addWidget(QtWidgets.QLabel("请设置透明度（0.1-1.0）："))
        layout.addWidget(spinbox)
        
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            dialog
        )
        buttons.accepted.connect(lambda: self.save_opacity(spinbox.value(), dialog))
        buttons.rejected.connect(dialog.reject)
        
        layout.addWidget(buttons)
        dialog.exec_()

    def save_interval(self, value, dialog):
        """保存提醒间隔设置"""
        self.reminder_interval = value
        self.progress_value = 0
        self.progress_bar.setValue(0)
        dialog.accept()

    def save_text(self, text, dialog):
        """保存提醒文字设置"""
        self.reminder_text_input.setText(text)
        dialog.accept()

    def save_opacity(self, value, dialog):
        """保存透明度设置"""
        self.transparency_input.setValue(value)
        self.setWindowOpacity(value)
        dialog.accept()

    def is_auto_start(self):
        """检查是否已设置开机自启"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.startup_reg_path,
                0,
                winreg.KEY_READ
            )
            value, _ = winreg.QueryValueEx(key, self.app_name)
            winreg.CloseKey(key)
            return value == self.app_path
        except WindowsError:
            return False

    def toggle_auto_start(self):
        """切换开机自启动状态"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.startup_reg_path,
                0,
                winreg.KEY_ALL_ACCESS
            )
            
            if self.startup_action.isChecked():
                # 添加到开机自启
                winreg.SetValueEx(
                    key,
                    self.app_name,
                    0,
                    winreg.REG_SZ,
                    self.app_path
                )
                QtWidgets.QMessageBox.information(
                    self,
                    "提示",
                    "已添加到开机自启动"
                )
            else:
                # 从开机自启动中移除
                try:
                    winreg.DeleteValue(key, self.app_name)
                    QtWidgets.QMessageBox.information(
                        self,
                        "提示",
                        "已取消开机自启动"
                    )
                except WindowsError:
                    pass
                    
            winreg.CloseKey(key)
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self,
                "错误",
                f"设置开机自启动失败：{str(e)}"
            )
            # 恢复复选框状态
            self.startup_action.setChecked(not self.startup_action.isChecked())

    def is_touch_device(self):
        """检测是否为触摸设备"""
        for device in QtGui.QTouchDevice.devices():
            if device.type() == QtGui.QTouchDevice.TouchScreen:
                return True
        return False


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    # 设置应用程序不随最后一个窗口关闭而退出
    app.setQuitOnLastWindowClosed(False)
    reminder_app = WaterReminderApp()
    sys.exit(app.exec_())
