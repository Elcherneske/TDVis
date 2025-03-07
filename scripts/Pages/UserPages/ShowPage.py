import streamlit as st
from .Heatmap_showpage import Heatmap

class ShowPage():
    def __init__(self):
        pass

    def run(self):
        self.show_show_page()
        
    # 在 ShowPage.py 的 show_show_page 方法中修改
    def show_show_page(self):
        st.title("展示页面")
        with st.sidebar:
            if st.button("重新选择", key="btn_reselect_show"):
                st.session_state['user_select_file'] = None
                st.rerun()
            if st.button("Heatmap", key="btn_heatmap_show"):
                st.session_state['current_page'] = 'heatmap'  # 设置导航状态
                st.rerun()
        # 如果当前页面不是 heatmap，才渲染默认内容
        if st.session_state.get('current_page') != 'heatmap':
            st.write("")

