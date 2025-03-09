import os
import streamlit as st

class FileUtils:
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