# 喝水提醒小助手

## 项目简介
一个简单而实用的桌面应用程序，用于提醒用户按时喝水。程序会在系统托盘显示图标，并在屏幕底部显示一个优雅的进度条。当到达设定的时间时，会弹出全屏提醒。

### 主要功能
- 可自定义提醒间隔（0.5-4小时）
- 自定义提醒文字
- 可调节界面透明度
- 支持开机自启动
- 每日喝水次数统计（午夜自动重置）
- 支持触摸屏操作
- 不影响正常工作（点击穿透）

## 运行环境
- Windows 操作系统
- Python 3.6+
- PyQt5
- pyinstaller (仅打包需要)

## 安装依赖
```
bash
pip install PyQt5
pip install pyinstaller # 如需打包成exe
```
## 项目文件结构
```
喝水提醒小助手/
├── 喝水提醒小助手.py # 主程序文件
├── 喝水提醒小助手.ico # 程序图标
├── build.py # 打包脚本
└── README.md # 项目说明文档
```
## 运行结果展示
![image](https://github.com/user-attachments/assets/453298b3-8a09-4b61-aa18-a0ff1adf73b1)
![image](https://github.com/user-attachments/assets/a8fd07ce-a87d-4f26-8f9d-847545f08fa9)
![image](https://github.com/user-attachments/assets/b46a6975-6636-494a-a6cc-5ea33d86eef6)
![image](https://github.com/user-attachments/assets/c83d1d22-517f-4094-9f81-f4f069827587)




## 如何运行

### 方式一：直接运行Python脚本
```
bash
python 喝水提醒小助手.py
```
### 方式二：打包成exe
1. 运行打包脚本：

```
bash
python build.py
```   
2. 在 `dist` 文件夹中找到生成的 `喝水提醒小助手.exe`
3. 将 `喝水提醒小助手.ico` 复制到与exe相同目录
4. 双击运行exe文件

## 使用说明
1. 首次运行会显示设置界面，可以设置：
   - 提醒间隔时间（默认3小时）
   - 提醒文字
   - 界面透明度
   - 进度条透明度

2. 设置完成后，程序会在：
   - 系统托盘显示图标
   - 屏幕底部显示进度条
   - 右下角显示今日喝水次数

3. 右键托盘图标可以：
   - 修改基础设置
   - 设置开机自启动
   - 退出程序

## 注意事项
1. 确保 `喝水提醒小助手.ico` 图标文件与程序在同一目录
2. 如需开机自启动，请确保程序有足够的权限
3. 程序会在午夜12点自动重置喝水计数
4. 进度条支持点击穿透，不会影响其他窗口的操作
5. 支持触摸屏设备，界面会自动适配

## 开发环境
- Python 3.12
- PyQt5 5.15.9
- Windows 10/11


## 技术支持
如遇到问题，请联系系统管理员lucianaib或提交 Issue。


