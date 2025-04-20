import streamlit as st
from ..FunctionPages.ReportPage import ReportPage
from ..FunctionPages.FileUtils import FileUtils
import os

class UserPage():
    def __init__(self):
        pass

    def run(self):
        self.init_session_state()
        self.show_user_page()

    def show_user_page(self):
        with st.sidebar:
            if st.button("退出登录"):
                st.session_state['authentication_status'] = None
                st.session_state['authentication_username'] = None
                st.session_state['user_select_file'] = None
                st.rerun()
        
        if not st.session_state['user_select_file']:
            st.title("文件选择界面")
            username = st.session_state.get('authentication_username', '')
            
            df = FileUtils.query_user_files(username)
            df.index = df.index + 1

            selected_file = st.radio(
                "**📃请选择您要查看报告的文件:**",
                df['file_name'],
                index=None,  # No default selection
                key="file_radio"
            )
            
            if st.button("选择文件"):
                if selected_file:
                    st.session_state['user_select_file'] = selected_file  # Store single file
                    st.rerun()
                else:
                    st.error("请先选择一个文件!")
        else:
            st.rerun()

    def init_session_state(self):
        if 'user_select_file' not in st.session_state:
            st.session_state['user_select_file'] = None
