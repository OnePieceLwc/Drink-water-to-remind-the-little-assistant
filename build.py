import PyInstaller.__main__
import sys
import os

# 确保在脚本所在目录运行
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 打包命令
PyInstaller.__main__.run([
    '喝水提醒小助手.py',  # 主程序文件
    '--name=喝水提醒小助手',  # 生成的exe名称
    '--windowed',  # 不显示控制台窗口
    '--noconsole',  # 不显示控制台
    '--icon=喝水提醒小助手.ico',  # 程序图标
    '--add-data=喝水提醒小助手.ico;.',  # 添加图标文件作为资源
    '--onefile',  # 打包成单个文件
    '--clean',  # 清理临时文件
    '--noconfirm',  # 不确认覆盖
]) 