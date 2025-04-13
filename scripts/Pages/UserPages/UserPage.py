import streamlit as st
from ..FunctionPages.ShowPage import ShowPage
from ..FunctionPages.FileUtils import FileUtils
import pandas as pd
import os

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
                st.session_state['authentication_username'] = None
                st.session_state['user_select_file'] = None
                st.rerun()
        
            
        if not st.session_state['user_select_file']:
            st.title("用户页面")
            st.write("请选择文件")
            username = st.session_state.get('authentication_username', '')
            df = FileUtils.query_user_files(username) 

            df.index = df.index + 1
            df["file_select"] = False
            config = {
                "file_name": st.column_config.TextColumn("文件名"),
                "file_select": st.column_config.CheckboxColumn("是否选择")
            }
            
            selec_df = st.data_editor(df, column_config=config, key="user_data_editor",width=800,height=300)
            selec_df[selec_df['file_select'] == True]['file_name'].tolist()
            if st.button("选择文件"):
                st.session_state['user_select_file'] = selec_df[selec_df['file_select'] == True]['file_name'].tolist()
                if st.session_state['user_select_file']:
                    st.rerun()
                else:
                    st.error("您尚未选择文件!")
        else:
            file_path = st.session_state['user_select_file'][0]
            file_suffix = os.path.splitext(file_path)[1]
            
            path=FileUtils.get_select_path()
            st.write(path)
            if file_suffix==".pptx":
                with open(path, 'rb') as file:
                    st.download_button( label="下载人工注释",
                                    data=file,
                                    file_name=file_path,
                                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
                                    )
            else:
                show_page = ShowPage()
                show_page.run()
    def init_session_state(self):
        if  'user_select_file' not in st.session_state:
            st.session_state['user_select_file'] = None