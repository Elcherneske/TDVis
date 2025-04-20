import os
import streamlit as st
import pandas as pd
import DBUtils as DBUtils
from Args import Args 

class FileUtils:
    """_summary_
    文件查询工具,用于统一维护文件查询路径
    注意:
    1. 所有文件路径均使用相对路径，避免硬编码
    2. 该文件查询依赖于会话状态authentication_username
    3. 之后可以添加缓存装饰器提升查询效率
    """
    @staticmethod
    def query_files(username=None):
        """
        通用文件查询方法
        :param username: 指定用户名时查询单个用户,None时查询所有用户
        :return: 包含(用户名, 文件名)的DataFrame
        """
        args = Args()  
        db_utils = DBUtils.DBUtils(args)  # 显式调用类名

        if username:
            file_addresses = db_utils.get_file_addresses(username)
            return pd.DataFrame([
                {"用户名": username, "文件名": os.path.normpath(f)}
                for f in file_addresses
            ])

        # 处理全部用户查询（管理员模式）
        all_files = []
        users = db_utils.query_users("", 0, 0)  # 获取所有用户
        for _, row in users.iterrows():
            file_addresses = db_utils.get_file_addresses(row['username'])
            all_files.extend([
                {"用户名": row['username'], "文件名": os.path.normpath(f)}
                for f in file_addresses
            ])
        
        return pd.DataFrame(all_files)

    @staticmethod  
    def query_user_files(username):
        """
        获取指定用户的文件列表
        :param username: 当前登录用户名
        :return: 包含文件名的DataFrame(列名为file_name)
        """
        args = Args()  
        db_utils = DBUtils.DBUtils(args) 
        file_addresses = db_utils.get_file_addresses(username)
        return pd.DataFrame({'file_name': [os.path.normpath(f) for f in file_addresses]})

    @staticmethod
    def get_html_report_path():
        """获取HTML报告路径"""
        # 获取用户选择的文件路径
        selected_file = st.session_state['user_select_file']
        #获取所有文件的列表
        all_files = os.listdir(selected_file)
        for filename in all_files:
            if filename.endswith("_html"):
                break
        return os.path.join(selected_file, filename)


