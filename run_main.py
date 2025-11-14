import streamlit.web.cli as stcli
import os
import sys
 
def get_base_path():
    """获取脚本运行的基础路径，支持 PyInstaller 打包"""
    if getattr(sys, 'frozen', False):  # 如果是 PyInstaller 打包的环境
        return sys._MEIPASS  # 获取临时目录路径
    return os.path.dirname(__file__)  # 普通运行环境
 
# 获取 QZCA_AI.py 的路径（适配打包环境） ###注意这里要改成你自己的应用py文件的名称
script_path = os.path.join(get_base_path(), "main.py")
 
def resolve_path(path):
    """解析相对路径为绝对路径"""
    resolved_path = os.path.abspath(os.path.join(os.getcwd(), path))
    return resolved_path
 
if __name__ == "__main__":
    # 检查 QZCA_AI.py 是否存在
    if not os.path.exists(script_path):
        print(f"Error: The script '{script_path}' does not exist!")
        sys.exit(1)
 
    # 构造 Streamlit 命令
    sys.argv = [
        "streamlit",
        "run",
        script_path,  # 替换为解析后的路径
        "--global.developmentMode=false",
    ]
 
    try:
        sys.exit(stcli.main())
    except Exception as e:
        print(f"Error while running Streamlit: {e}")
        sys.exit(1)