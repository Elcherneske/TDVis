import os
import streamlit as st#重复引用如何剥开?
import pandas as pd

class FileUtils:
    """_summary_
    文件查询工具,用于统一维护文件查询路径
    注意:
    1. 所有文件路径均使用相对路径，避免硬编码
    2. 该文件查询依赖于会话状态authentication_username
    3.之后可以添加缓存装饰器提升查询效率
    """
    @staticmethod
    def query_files(username=None):
        """
        通用文件查询方法
        :param username: 指定用户名时查询单个用户，None时查询所有用户,后续可以通过输入用户名进行查询.并且给出输出df的导出方式
        :return: 包含(用户名, 文件名)的DataFrame
        """
        files_path = FileUtils.get_files_path()
        all_files = []

        # 处理单个用户查询
        if username:
            user_path = os.path.join(files_path, username)
            if os.path.exists(user_path):
                return pd.DataFrame([
                    {"用户名": username, "文件名": f}
                    for f in os.listdir(user_path)
                ])
            return pd.DataFrame(columns=["用户名", "文件名"])

        # 处理全部用户查询（管理员模式）
        for user_folder in os.listdir(files_path):
            user_path = os.path.join(files_path, user_folder)
            if os.path.isdir(user_path):
                all_files.extend([
                    {"用户名": user_folder, "文件名": f}
                    for f in os.listdir(user_path)
                ])
        
        return pd.DataFrame(all_files)
    def query_user_files(username):
        """
        获取指定用户的文件列表
        :param username: 当前登录用户名
        :return: 包含文件名的DataFrame（列名为file_name）
        """
        files_path = os.path.join(
            os.path.dirname(__file__), 
            '..', '..', '..', 
            'files', 
            username
        )
        
        if not os.path.exists(files_path):
            return pd.DataFrame(columns=["file_name"])
            
        files = [
            {"file_name": f} 
            for f in os.listdir(files_path)
            if not f.startswith('.')  # 过滤隐藏文件
        ]
        return pd.DataFrame(files)
    @staticmethod
    def get_select_path():
        """获取用户选择的文件路径"""
        if 'user_select_file' not in st.session_state or not st.session_state['user_select_file']:
            return None
            
        path = st.session_state['user_select_file'][0]
        username = st.session_state['authentication_username']
        return os.path.join(
            os.path.dirname(__file__), '..', '..', '..', 
            'files', username, path
        )
    @staticmethod
    def get_html_report_path():
        """获取HTML报告路径"""
        base_path = FileUtils.get_select_path()
        if not base_path or not os.path.exists(base_path):
            return None
        
        # 获取目录下所有文件
        all_files = os.listdir(base_path)
        for filename in all_files:
            if filename.endswith("_html"):
                break

        base_dir = os.path.join(
            os.path.dirname(__file__), '..', '..', '..',
            'files', 
            st.session_state['authentication_username'],
            st.session_state['user_select_file'][0],
            filename  # 添加_html后缀
        )
        return base_dir

    @staticmethod
    def get_files_path():
        """统一获取files目录路径"""
        return os.path.join(
            os.path.dirname(__file__), '..', '..', '..', 'files'
        )

