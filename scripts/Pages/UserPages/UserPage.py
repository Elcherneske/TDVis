import streamlit as st
from .ShowPage import ShowPage

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
            files = ["文件1", "文件2", "文件3", "文件4", "文件5", "文件6", "文件7", "文件8", "文件9", "文件10"]
            selected_file = st.radio("选择文件", files)
            if st.button("选择文件"):
                st.session_state['user_select_file'] = selected_file
                st.rerun()
        else:
            show_page = ShowPage()
            show_page.run()

    def init_session_state(self):
        if 'user_select_file' not in st.session_state:
            st.session_state['user_select_file'] = None
            
            
