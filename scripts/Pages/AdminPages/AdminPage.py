import streamlit as st
import pandas as pd
class AdminPage():
    def __init__(self):
        pass

    def run(self):
        self.show_admin_page()

    def show_admin_page(self):
        # 侧边栏退出按钮
        with st.sidebar:
            if st.button("退出"):
                st.session_state['authentication_status'] = None
                st.rerun()

        # 主页面标题
        st.title("管理员页面")

        # 用户列表
        df = pd.DataFrame(
            {
                "username": ["admin", "user1", "user2"],
                "role": ["管理员", "普通用户", "普通用户"],
                "is_selected": [False, False, False]
            }
        )

        config = {
            "username": st.column_config.TextColumn("用户名"),
            "role": st.column_config.SelectboxColumn("角色", options=["管理员", "普通用户"]),
            "is_selected": st.column_config.CheckboxColumn("是否")
        }

        st.data_editor(df, column_config=config)

        # 删除用户按钮
        if st.button("修改用户"):
            st.write("修改用户")

        add_form = st.form("add_form")
        add_form.text_input("用户名")
        add_form.selectbox("角色", options=["管理员", "普通用户"])

        # 添加用户按钮
        if add_form.form_submit_button("添加用户"):
            st.write("添加用户")
