import streamlit as st
import pandas as pd
import numpy as np
import os


class ToppicShowPage():
        def __init__(self):
            self.selected_file = None
            self.df = None
        def run(self):
            self.show_toppic()
        def show_toppic(self):
            with st.sidebar:
                st.button("退出", key="exit", 
                    on_click=lambda: st.session_state.update({
                        'authentication_status': None,
                        'current_page': None
                    }))
                st.button("重新选样", key="reselect", 
                        on_click=lambda: st.session_state.update({
                            'user_select_file': None,
                            'current_page': st.session_state['authentication_role']
                        }))
                st.button("返回报告界面",key="return_showpage",on_click=lambda: st.session_state.update({
                        'current_page': None
                    }))
            if st.button("📊 查看TOPPIC报告", key="btn_show_toppic"):
                report_path = self._get_toppic_report_path()
                if report_path:
                    self._display_html_report(report_path)
                else:
                    st.error("未找到TOPPIC报告文件")