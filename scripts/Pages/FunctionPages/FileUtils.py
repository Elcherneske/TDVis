import os
import streamlit as st
import pandas as pd
import DBUtils as DBUtils
from Args import Args 

class FileUtils:
    """_summary_
    文件查询工具,用于统一维护文件查询路径
    可以查询用户名下对应的文件地址

    """


    @staticmethod
    def query_files(username=None):
        """
        通用文件**地址**查询方法
        是为数据库操作
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
        设计数据库操作
        :param username: 当前登录用户名
        :return: 包含文件名的DataFrame(列名为file_name)
        """
        args = Args()  
        db_utils = DBUtils.DBUtils(args) 
        file_addresses = db_utils.get_file_addresses(username)
        return pd.DataFrame({'file_name': [os.path.normpath(f) for f in file_addresses]})

    @staticmethod
    def list_samples(selected_path=None):
        """
        Args:
            selected_path (str): 指定要查询的文件夹路径。接收数据库中所存储的主文件夹路径
        Returns:
            list: 包含所有检测样品的名称列表(默认使用下划线来进行划分)
        """
        samples = []
        if not os.path.exists(selected_path):
            raise FileNotFoundError(f"路径不存在: {selected_path}")
        for filename in os.listdir(selected_path):
            if filename.endswith("ms1.feature"):
                # 默认借助于下划线来进行样品名称的拆分
                sample_name = filename.split("_")[0]
                samples.append(sample_name)
        return samples

    @staticmethod
    def get_html_report_path(selected_path=None,sample_name=None):

        target_suffix = f"{sample_name}_html"
        for filename in os.listdir(selected_path):
            if filename.endswith(target_suffix):
                return os.path.join(selected_path, filename)
        raise FileNotFoundError(f"未找到HTML报告文件: {target_suffix}")


    @staticmethod
    def get_file_path(suffix,selected_path=None,sample_name=None):
        """
        获取指定后缀文件的路径
        针对于最开始选中的文件夹,也就是一级文件夹!
        Args:
            suffix (str): 指定的文件后缀，如 ".feature"
            selected_path (str): 指定的文件夹路径，默认为 None，使用 session_state 中的值
            sample_name (str): 指定的样品名称，默认为 None，使用 session_state 中的值
        Returns:
            str: 找到的文件路径
        """
        target_suffix = f"{sample_name}{suffix}"
        for filename in os.listdir(selected_path):
            if filename.endswith(target_suffix):
                return os.path.join(selected_path, filename)
        raise FileNotFoundError(f"未找到指定后缀文件: {target_suffix}")


    # def _get_feature_files(self, selected_path=None,sample_name=None):
    #     """
    #     获取指定文件夹下的所有.feature 文件
    #     Args:
    #         selected_path (str): 指定的文件夹路径
    #     Returns:
    #         list: 包含所有.feature 文件路径的列表
    #     """
    #     if not os.path.exists(selected_path):
    #         raise FileNotFoundError(f"路径不存在: {selected_path}"):
    #     """获取当前样品所对应的两个feature文件"""
    #     if not os.path.exists(files_path):
    #         return []
    #     return [
    #         os.path.join(files_path, f) 
    #         for f in os.listdir(files_path) 
    #         if f.endswith('.feature') or f.endswith('.FEATURE') 
    #     ]




