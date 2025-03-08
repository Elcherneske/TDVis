import streamlit as st
from .ShowPage import ShowPage
import os
import pandas as pd

class UserPage():
    def __init__(self):
        pass

    def run(self):
        self.init_session_state()
        self.show_user_page()

    def show_user_page(self):
        
        with st.sidebar:
            if st.button("退出"):
                st.session_state['authentication_status'] = None
                st.rerun()
            
        
        if st.session_state['user_select_file'] is None:
            # todo: 这里用一个dataframe把文件列表展示出来，要求一次只展示10个，可以通过滚动或者翻页展示更多
            st.title("用户页面")
            st.write("请选择文件")
            files_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'files')
            files = os.listdir(files_path)
            username = st.session_state.get('authentication_username', '')
            user_files_path = os.path.join(files_path, username)
            if os.path.exists(user_files_path):
                files = os.listdir(user_files_path)
            else:
                files = []
            # 创建DataFrame
            df = pd.DataFrame(files, columns=["file_name"])
            df.index = df.index + 1
            df["file_select"] = False
            config = {
                "file_name": st.column_config.TextColumn("文件名"),
                "file_select": st.column_config.CheckboxColumn("是否选择")
            }
            selec_df = st.data_editor(df, column_config=config, key="user_data_editor",width=800)
            # 使用滑动展示
            df = df.head(10)  # 只展示前10个文件
            if st.button("选择文件"):
                st.session_state['user_select_file'] = selec_df[selec_df['file_select'] == True]['file_name'].tolist()
                st.rerun()
        else:
            show_page = ShowPage()
            show_page.run()

    def init_session_state(self):
        if  'user_select_file' not in st.session_state:
            st.session_state['user_select_file'] = None